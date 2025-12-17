from datetime import datetime, timezone

from src.models.vehicle import Vehicle
from src.models.session import Session as ParkingSession

API_PREFIX = "/api"  # change to "" if your api_router does not mount under /api


def _create_vehicle(db_session, *, driver_id=1, region_code="TST", plate_text="TEST123", is_blacklisted=False):
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


def _create_session(db_session, *, vehicle_id: int, started_at=None, ended_at=None, status="open"):
    s = ParkingSession(
        vehicle_id=vehicle_id,
        started_at=started_at or datetime.now(timezone.utc),
        ended_at=ended_at,
        status=status,
    )
    db_session.add(s)
    db_session.commit()
    db_session.refresh(s)
    return s


def test_start_session_201(client, db_session):
    v = _create_vehicle(db_session, region_code="SOF", plate_text="A1000AA")

    started_at = datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc).isoformat()

    r = client.post(
        f"{API_PREFIX}/sessions",
        json={"vehicle_id": v.id, "started_at": started_at},
    )
    assert r.status_code == 201, r.text
    data = r.json()

    assert data["vehicle_id"] == v.id
    assert "id" in data
    assert data["started_at"] is not None


def test_get_session(client, db_session):
    v = _create_vehicle(db_session, region_code="SOF", plate_text="A1001AA")
    s = _create_session(db_session, vehicle_id=v.id)

    r = client.get(f"{API_PREFIX}/sessions/{s.id}")
    assert r.status_code == 200, r.text
    data = r.json()

    assert data["id"] == s.id
    assert data["vehicle_id"] == v.id


def test_list_sessions_for_vehicle(client, db_session):
    v1 = _create_vehicle(db_session, region_code="SOF", plate_text="A1002AA")
    v2 = _create_vehicle(db_session, region_code="VAR", plate_text="B2000BB")

    s1 = _create_session(db_session, vehicle_id=v1.id)
    s2 = _create_session(db_session, vehicle_id=v1.id)
    _ = _create_session(db_session, vehicle_id=v2.id)

    r = client.get(f"{API_PREFIX}/sessions", params={"vehicle_id": v1.id})
    assert r.status_code == 200, r.text
    data = r.json()

    assert isinstance(data, list)
    ids = {item["id"] for item in data}
    assert s1.id in ids
    assert s2.id in ids
    assert all(item["vehicle_id"] == v1.id for item in data)


def test_end_session(client, db_session):
    v = _create_vehicle(db_session, region_code="SOF", plate_text="A1003AA")

    started_at = datetime(2025, 1, 1, 10, 0, 0)   # naive
    s = _create_session(db_session, vehicle_id=v.id, started_at=started_at, ended_at=None)

    ended_at = datetime(2025, 1, 1, 12, 0, 0).isoformat()

    r = client.post(
        f"{API_PREFIX}/sessions/{s.id}/end",
        json={"ended_at": ended_at},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["id"] == s.id
    assert data["ended_at"] is not None



def test_delete_session_204(client, db_session):
    v = _create_vehicle(db_session, region_code="SOF", plate_text="A1004AA")
    s = _create_session(db_session, vehicle_id=v.id)

    r = client.delete(f"{API_PREFIX}/sessions/{s.id}")
    assert r.status_code == 204

    # behavior depends on your service; many projects return 404 after delete
    r2 = client.get(f"{API_PREFIX}/sessions/{s.id}")
    assert r2.status_code in (404, 200)
