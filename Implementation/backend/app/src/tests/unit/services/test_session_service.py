from datetime import datetime, timezone, timedelta
import pytest
from fastapi import HTTPException

from src.services.sessions import ParkingSessionService


class FakeDB:
    def __init__(self, vehicles=None):
        self.vehicles = vehicles or {}

    def get(self, model, pk):
        # Vehicle existence check only
        return self.vehicles.get(pk)


class FakeRepo:
    def __init__(self, db):
        self.db = db
        self.active_for_vehicle = {}
        self.sessions_by_id = {}
        self.created = []
        self.ended = []
        self.deleted = []

    def get_active_for_vehicle(self, vehicle_id):
        return self.active_for_vehicle.get(vehicle_id)

    def create(self, **kwargs):
        # minimal fake Session object
        s = type("Session", (), {})()
        s.id = len(self.created) + 1
        s.vehicle_id = kwargs["vehicle_id"]
        s.started_at = kwargs.get("started_at") or datetime.now(timezone.utc)
        s.ended_at = None
        self.created.append(kwargs)
        self.sessions_by_id[s.id] = s
        self.active_for_vehicle[s.vehicle_id] = s
        return s

    def get(self, session_id):
        return self.sessions_by_id.get(session_id)

    def list_by_vehicle(self, vehicle_id):
        return [s for s in self.sessions_by_id.values() if s.vehicle_id == vehicle_id]

    def end_session(self, s, ended_at):
        s.ended_at = ended_at
        self.ended.append((s.id, ended_at))
        # no longer active
        self.active_for_vehicle.pop(s.vehicle_id, None)
        return s

    def delete(self, s):
        self.deleted.append(s.id)
        self.sessions_by_id.pop(s.id, None)
        self.active_for_vehicle.pop(s.vehicle_id, None)


def test_start_session_vehicle_not_found_404():
    db = FakeDB(vehicles={})  # no vehicles
    repo = FakeRepo(db)
    svc = ParkingSessionService(repo)

    with pytest.raises(HTTPException) as e:
        svc.start(vehicle_id=1)

    assert e.value.status_code == 404
    assert e.value.detail == "Vehicle not found"


def test_start_session_conflict_if_active_exists_409():
    db = FakeDB(vehicles={1: object()})
    repo = FakeRepo(db)

    # create one active session
    first = repo.create(vehicle_id=1)
    repo.active_for_vehicle[1] = first

    svc = ParkingSessionService(repo)

    with pytest.raises(HTTPException) as e:
        svc.start(vehicle_id=1)

    assert e.value.status_code == 409


def test_end_session_rejects_end_before_start_400():
    db = FakeDB(vehicles={1: object()})
    repo = FakeRepo(db)
    svc = ParkingSessionService(repo)

    s = repo.create(vehicle_id=1, started_at=datetime(2025, 1, 2, tzinfo=timezone.utc))

    with pytest.raises(HTTPException) as e:
        svc.end(s.id, ended_at=datetime(2025, 1, 1, tzinfo=timezone.utc))

    assert e.value.status_code == 400
    assert e.value.detail == "ended_at must be >= started_at"


def test_end_session_sets_ended_at_ok():
    db = FakeDB(vehicles={1: object()})
    repo = FakeRepo(db)
    svc = ParkingSessionService(repo)

    start = datetime.now(timezone.utc) - timedelta(hours=1)
    s = repo.create(vehicle_id=1, started_at=start)

    end = datetime.now(timezone.utc)
    out = svc.end(s.id, ended_at=end)

    assert out.ended_at == end
