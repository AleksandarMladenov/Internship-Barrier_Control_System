from datetime import datetime, timedelta
from enum import Enum

from src.core.security import hash_password
from src.core.settings import settings

API_PREFIX = "/api"  # change to "" if your api_router is not mounted under /api


def test_login_invalid_credentials_401(client):
    r = client.post(f"{API_PREFIX}/auth/login", json={"email": "nope@example.com", "password": "wrong"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Incorrect email or password"


def test_logout_ok(client):
    r = client.post(f"{API_PREFIX}/auth/logout")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_me_uses_current_admin_override(client):
    from src.core.security import get_current_admin

    class Role(Enum):
        admin = "admin"

    class FakeAdmin:
        id = 1
        name = "Test Admin"
        email = "admin@example.com"
        role = Role.admin
        is_active = True

    client.app.dependency_overrides[get_current_admin] = lambda: FakeAdmin()

    r = client.get(f"{API_PREFIX}/auth/me")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == 1
    assert data["email"] == "admin@example.com"
    assert data["role"] == "admin"
    assert data["is_active"] is True

    client.app.dependency_overrides.pop(get_current_admin, None)


def _create_admin(db_session, *, email: str, password_plain: str, is_active: bool = True, name: str = "A"):
    from src.models.admin import Admin  # adjust if your import differs

    admin = Admin(
        email=email,
        password=hash_password(password_plain),
        is_active=is_active,
        name=name,
        # If your Admin model requires role/status/etc, add them here.
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


def test_login_sets_cookie_ok(client, db_session):
    _create_admin(db_session, email="ok@example.com", password_plain="pass123", is_active=True)

    r = client.post(f"{API_PREFIX}/auth/login", json={"email": "ok@example.com", "password": "pass123"})
    assert r.status_code == 200, r.text
    assert r.json()["ok"] is True

    set_cookie = r.headers.get("set-cookie", "")
    assert settings.AUTH_COOKIE_NAME in set_cookie


def test_login_disabled_403(client, db_session):
    _create_admin(db_session, email="disabled@example.com", password_plain="pass123", is_active=False)

    r = client.post(f"{API_PREFIX}/auth/login", json={"email": "disabled@example.com", "password": "pass123"})
    assert r.status_code == 403
    assert r.json()["detail"] == "Account disabled"


def _create_invited_admin(db_session, *, token: str, expires_at: datetime):
    from src.models.admin import Admin, AdminStatus  # adjust if your import differs

    admin = Admin(
        email="invitee@example.com",
        password="",
        is_active=False,
        name="",
        status=AdminStatus.invited,
        invited_token=token,
        invited_expires_at=expires_at,  # SQLite often returns this as naive
        # If your Admin model requires role, set it here.
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


def _patch_auth_datetime_now_to_naive(monkeypatch):
    """
    Patch src.api.routers.auth.datetime.now(...) so it returns naive datetime.
    This avoids comparing naive (SQLite) vs aware (timezone.utc) datetimes.
    """
    import src.api.routers.auth as auth_module

    class FakeDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            # ignore tz and return naive utc time
            return datetime.utcnow()

    monkeypatch.setattr(auth_module, "datetime", FakeDateTime)


def test_accept_invite_invalid_token_400(client):
    r = client.post(
        f"{API_PREFIX}/auth/accept-invite",
        json={"token": "nope", "name": "X", "password": "NewPass123"},
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "Invalid or already used invite"


def test_accept_invite_expired_400(client, db_session, monkeypatch):
    _patch_auth_datetime_now_to_naive(monkeypatch)

    _create_invited_admin(
        db_session,
        token="expired-token",
        expires_at=datetime.utcnow() - timedelta(minutes=1),  # naive
    )

    r = client.post(
        f"{API_PREFIX}/auth/accept-invite",
        json={"token": "expired-token", "name": "X", "password": "NewPass123"},
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "Invite expired"


def test_accept_invite_ok_sets_cookie(client, db_session, monkeypatch):
    _patch_auth_datetime_now_to_naive(monkeypatch)

    _create_invited_admin(
        db_session,
        token="good-token",
        expires_at=datetime.utcnow() + timedelta(hours=1),  # naive
    )

    r = client.post(
        f"{API_PREFIX}/auth/accept-invite",
        json={"token": "good-token", "name": "Invited User", "password": "NewPass123"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["ok"] is True

    set_cookie = r.headers.get("set-cookie", "")
    assert settings.AUTH_COOKIE_NAME in set_cookie
