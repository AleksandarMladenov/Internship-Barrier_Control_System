import pytest

from src.models import Vehicle
from src.repositories.subscription_sqlalchemy import SubscriptionRepository


API_PREFIX = "/api"  # change to "" if your api_router does not mount under /api


def _create_vehicle(db_session, *, driver_id: int, region_code: str, plate_text: str, is_blacklisted: bool = False) -> Vehicle:
    v = Vehicle(
        driver_id=driver_id,
        region_code=region_code,
        plate_text=plate_text,
        is_blacklisted=is_blacklisted,
    )
    db_session.add(v)
    db_session.commit()
    db_session.refresh(v)
    return v


def test_get_vehicle_not_found(client):
    r = client.get(f"{API_PREFIX}/vehicles/999999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Vehicle not found"


def test_get_vehicle_success(client, db_session):
    v = _create_vehicle(db_session, driver_id=1, region_code="CA", plate_text="1234AB", is_blacklisted=False)

    r = client.get(f"{API_PREFIX}/vehicles/{v.id}")
    assert r.status_code == 200
    data = r.json()

    # VehicleRead should at least include these
    assert data["id"] == v.id
    assert data["driver_id"] == 1
    assert data["region_code"] == "CA"
    assert data["plate_text"] == "1234AB"


def test_list_vehicles_basic(client, db_session, monkeypatch):
    v1 = _create_vehicle(db_session, driver_id=1, region_code="CA", plate_text="1234AB", is_blacklisted=False)
    v2 = _create_vehicle(db_session, driver_id=2, region_code="CB", plate_text="9999ZZ", is_blacklisted=False)

    # Make access_status deterministic: v1 authorized, v2 pending
    def fake_has_active_now(self, vehicle_id: int) -> bool:
        return vehicle_id == v1.id

    monkeypatch.setattr(SubscriptionRepository, "has_active_now", fake_has_active_now)

    r = client.get(f"{API_PREFIX}/vehicles")
    assert r.status_code == 200
    payload = r.json()

    assert "items" in payload
    assert "total" in payload
    assert payload["total"] >= 2

    # Ensure our two vehicles are present and have derived status
    by_id = {item["id"]: item for item in payload["items"]}
    assert by_id[v1.id]["access_status"] == "authorized"
    assert by_id[v2.id]["access_status"] == "pending"


def test_list_vehicles_status_filter(client, db_session, monkeypatch):
    v_auth = _create_vehicle(db_session, driver_id=1, region_code="CA", plate_text="1111AA", is_blacklisted=False)
    v_pending = _create_vehicle(db_session, driver_id=1, region_code="CA", plate_text="2222BB", is_blacklisted=False)
    v_suspended = _create_vehicle(db_session, driver_id=1, region_code="CA", plate_text="3333CC", is_blacklisted=True)

    # authorized only for v_auth, pending for v_pending; v_suspended should always be suspended
    def fake_has_active_now(self, vehicle_id: int) -> bool:
        return vehicle_id == v_auth.id

    monkeypatch.setattr(SubscriptionRepository, "has_active_now", fake_has_active_now)

    r = client.get(f"{API_PREFIX}/vehicles", params={"status": "authorized"})
    assert r.status_code == 200
    items = r.json()["items"]
    assert all(i["access_status"] == "authorized" for i in items)
    assert any(i["id"] == v_auth.id for i in items)

    r = client.get(f"{API_PREFIX}/vehicles", params={"status": "pending"})
    assert r.status_code == 200
    items = r.json()["items"]
    assert all(i["access_status"] == "pending" for i in items)
    assert any(i["id"] == v_pending.id for i in items)

    r = client.get(f"{API_PREFIX}/vehicles", params={"status": "suspended"})
    assert r.status_code == 200
    items = r.json()["items"]
    assert all(i["access_status"] == "suspended" for i in items)
    assert any(i["id"] == v_suspended.id for i in items)


def test_list_vehicles_search_and_driver_filter(client, db_session, monkeypatch):
    # deterministic status
    monkeypatch.setattr(SubscriptionRepository, "has_active_now", lambda self, vehicle_id: False)

    v1 = _create_vehicle(db_session, driver_id=10, region_code="SOF", plate_text="A1234BC", is_blacklisted=False)
    _ = _create_vehicle(db_session, driver_id=11, region_code="VAR", plate_text="X9999YY", is_blacklisted=False)

    # search by plate fragment
    r = client.get(f"{API_PREFIX}/vehicles", params={"q": "a123"})
    assert r.status_code == 200
    items = r.json()["items"]
    assert any(i["id"] == v1.id for i in items)

    # filter by driver_id
    r = client.get(f"{API_PREFIX}/vehicles", params={"driver_id": 10})
    assert r.status_code == 200
    items = r.json()["items"]
    assert all(i["driver_id"] == 10 for i in items)
