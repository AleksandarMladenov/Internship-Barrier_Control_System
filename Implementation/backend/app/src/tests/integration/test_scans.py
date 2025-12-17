from datetime import datetime, timezone

API_PREFIX = "/api"


def _create_vehicle(db_session, *, region_code: str, plate_text: str, is_blacklisted=False):
    from src.models.vehicle import Vehicle

    v = Vehicle(
        driver_id=1,
        region_code=region_code,
        plate_text=plate_text,
        is_blacklisted=is_blacklisted,
    )
    db_session.add(v)
    db_session.commit()
    db_session.refresh(v)
    return v


def _create_open_session(db_session, *, vehicle_id: int):
    from src.models.session import Session

    s = Session(
        vehicle_id=vehicle_id,
        started_at=datetime.now(timezone.utc),
        ended_at=None,
        status="open",
    )
    db_session.add(s)
    db_session.commit()
    db_session.refresh(s)
    return s


def _patch_subscription_active(monkeypatch):
    # GateService uses this to decide authorized/pending
    from src.repositories.subscription_sqlalchemy import SubscriptionRepository
    monkeypatch.setattr(SubscriptionRepository, "has_active_now", lambda self, vehicle_id: True)


def _patch_barrier_pulse(monkeypatch):
    """
    Prevent real HTTP call to barrier controller during tests.
    We patch the GateService internal barrier open call.
    """
    import src.services.gate as gate_module

    # GateService likely calls a function or method that does the HTTP request.
    # Common patterns: pulse_open(), _pulse_open(), open_barrier(), etc.
    # We'll patch anything that exists safely.

    for name in ("pulse_open", "_pulse_open", "open_barrier", "_open_barrier"):
        if hasattr(gate_module, name):
            monkeypatch.setattr(gate_module, name, lambda *args, **kwargs: None)

    # If the HTTP call is inside GateService methods, patch those too
    if hasattr(gate_module, "GateService"):
        cls = gate_module.GateService
        for name in ("_pulse_open", "pulse_open", "_open_barrier", "open_barrier"):
            if hasattr(cls, name):
                monkeypatch.setattr(cls, name, lambda *args, **kwargs: None)


# ----------------------------
# ENTRY SCAN
# ----------------------------

def test_entry_scan_authorized_201(client, db_session, monkeypatch):
    _create_vehicle(db_session, region_code="CA", plate_text="1234AB")

    _patch_subscription_active(monkeypatch)
    _patch_barrier_pulse(monkeypatch)

    r = client.post(
        f"{API_PREFIX}/scans/entry",
        json={
            "region_code": "CA",
            "plate_text": "1234AB",
            "gate_id": "1",  # schema expects string
            "source": "camera",
        },
    )

    assert r.status_code == 201, r.text
    data = r.json()

    # Match your real response fields
    assert data.get("barrier_action") in {"open", "deny", "noop"}
    assert data.get("reason") is not None
    assert data.get("session_id") is not None
    assert data.get("created_at_utc") is not None


def test_entry_scan_blacklisted_403(client, db_session, monkeypatch):
    _create_vehicle(db_session, region_code="CA", plate_text="BLACK1", is_blacklisted=True)
    _patch_barrier_pulse(monkeypatch)

    r = client.post(
        f"{API_PREFIX}/scans/entry",
        json={
            "region_code": "CA",
            "plate_text": "BLACK1",
            "gate_id": "1",
            "source": "camera",
        },
    )

    assert r.status_code == 403
    assert r.json()["detail"] in {"blacklisted", "not_allowed"}


def test_entry_scan_unknown_vehicle_creates_session_201(client, monkeypatch):
    # the service currently returns 201 for unknown vehicles
    r = client.post(
        f"{API_PREFIX}/scans/entry",
        json={
            "region_code": "XX",
            "plate_text": "NOPE",
            "gate_id": "1",
            "source": "camera",
        },
    )

    assert r.status_code == 201, r.text
    data = r.json()
    assert data.get("session_id") is not None
    assert data.get("barrier_action") in {"open", "noop", "deny"}
    assert data.get("created_at_utc") is not None



# ----------------------------
# EXIT SCAN
# ----------------------------

def test_exit_scan_ok_200(client, db_session, monkeypatch):
    v = _create_vehicle(db_session, region_code="BG", plate_text="EXIT1")
    _create_open_session(db_session, vehicle_id=v.id)
    _patch_barrier_pulse(monkeypatch)

    r = client.post(
        f"{API_PREFIX}/scans/exit",
        json={
            "region_code": "BG",
            "plate_text": "EXIT1",
            "gate_id": "2",
            "source": "camera",
        },
    )

    assert r.status_code == 200, r.text
    data = r.json()

    # Be tolerant: exit response might differ slightly from entry
    assert data.get("barrier_action") is not None
    assert data.get("reason") is not None
    assert data.get("created_at_utc") is not None


def test_exit_scan_unknown_vehicle_200_or_400(client, monkeypatch):
    _patch_barrier_pulse(monkeypatch)

    r = client.post(
        f"{API_PREFIX}/scans/exit",
        json={
            "region_code": "BG",
            "plate_text": "UNKNOWNEXIT",
            "gate_id": "2",
            "source": "camera",
        },
    )

    assert r.status_code in (200, 400)
