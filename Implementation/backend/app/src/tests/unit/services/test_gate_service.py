# src/tests/unit/test_gate_service.py
from datetime import datetime, timezone
import pytest
from fastapi import HTTPException

import src.services.gate as gate_module


# ----------------------------
# Fakes
# ----------------------------

class FakeDB:
    def refresh(self, obj):
        return

    def commit(self):
        return


class FakeVehicle:
    def __init__(self, id=1, is_blacklisted=False):
        self.id = id
        self.is_blacklisted = is_blacklisted


class FakeSession:
    def __init__(self, id=1, started_at=None, ended_at=None, status=None):
        self.id = id
        self.started_at = started_at or datetime.now(timezone.utc)
        self.ended_at = ended_at
        self.status = status
        self.plan = None
        self.plan_id = None
        self.duration = None
        self.amount_charged = None


class FakeVehicleRepo:
    def __init__(self, vehicle=None):
        self.vehicle = vehicle
        self.created = []

    def get_by_plate(self, region_code, plate_text):
        return self.vehicle

    def create(self, **kwargs):
        v = FakeVehicle(id=99, is_blacklisted=False)
        self.created.append(kwargs)
        self.vehicle = v
        return v


class FakeDriverRepo:
    def __init__(self):
        self.created = []
        self._driver = type("Driver", (), {"id": 10})()

    def get_by_email(self, email):
        return None

    def create(self, name, email):
        self.created.append((name, email))
        return self._driver


class FakeSessionRepo:
    def __init__(self, active=None):
        self.active = active
        self.created = []
        self.ended = []
        self.latest_awaiting = None

    def get_active_for_vehicle(self, vehicle_id):
        return self.active

    def create(self, vehicle_id, started_at=None):
        s = FakeSession(id=1, started_at=started_at)
        self.created.append((vehicle_id, started_at))
        self.active = s
        return s

    def get_latest_awaiting_payment_for_vehicle(self, vehicle_id):
        return self.latest_awaiting

    def end_session(self, s, ended_at):
        s.ended_at = ended_at
        self.ended.append((s.id, ended_at))
        self.active = None
        return s


class FakeSubsRepo:
    def __init__(self, active_sub=False):
        self.active_sub = active_sub

    def get_active_subscription_plan_for_vehicle_at(self, vehicle_id, now):
        return object() if self.active_sub else None


class FakeVisitorPlan:
    def __init__(self, id=1, price_per_minute_cents=10, currency="EUR"):
        self.id = id
        self.price_per_minute_cents = price_per_minute_cents
        self.currency = currency


class FakePlanRepo:
    def __init__(self, visitor_plan=None):
        self.visitor_plan = visitor_plan

    def get_default_visitor_plan(self):
        return self.visitor_plan


# ----------------------------
# Tests
# ----------------------------

def _patch_barrier(monkeypatch):
    monkeypatch.setattr(gate_module, "_barrier_pulse_open", lambda *a, **k: None)
    monkeypatch.setattr(gate_module, "_barrier_force_close", lambda *a, **k: None)


def test_entry_blacklisted_403(monkeypatch):
    _patch_barrier(monkeypatch)

    svc = gate_module.GateService(FakeDB())
    svc.vehicles = FakeVehicleRepo(vehicle=FakeVehicle(id=1, is_blacklisted=True))
    svc.sessions = FakeSessionRepo(active=None)
    svc.drivers = FakeDriverRepo()
    svc.subs = FakeSubsRepo()
    svc.plans = FakePlanRepo()

    with pytest.raises(HTTPException) as e:
        svc.handle_entry_scan(region_code="CA", plate_text="1234AB", gate_id="1", source="camera")

    assert e.value.status_code == 403
    assert e.value.detail == "blacklisted"


def test_entry_reuses_existing_open_session(monkeypatch):
    _patch_barrier(monkeypatch)

    existing = FakeSession(id=7, started_at=datetime.now(timezone.utc))
    svc = gate_module.GateService(FakeDB())
    svc.vehicles = FakeVehicleRepo(vehicle=FakeVehicle(id=1, is_blacklisted=False))
    svc.sessions = FakeSessionRepo(active=existing)
    svc.drivers = FakeDriverRepo()
    svc.subs = FakeSubsRepo()
    svc.plans = FakePlanRepo()

    out = svc.handle_entry_scan(region_code="ca", plate_text=" 1234ab ", gate_id="1", source="camera")
    assert out["reason"] == "existing_open_session"
    assert out["session_id"] == 7
    assert out["barrier_action"] == "open"


def test_entry_unknown_vehicle_creates_visitor_vehicle(monkeypatch):
    _patch_barrier(monkeypatch)

    svc = gate_module.GateService(FakeDB())
    svc.vehicles = FakeVehicleRepo(vehicle=None)  # unknown
    svc.sessions = FakeSessionRepo(active=None)
    svc.drivers = FakeDriverRepo()
    svc.subs = FakeSubsRepo()
    svc.plans = FakePlanRepo()

    out = svc.handle_entry_scan(region_code="xx", plate_text="nope", gate_id="1", source="camera")

    assert out["reason"] == "created"
    assert out["session_id"] == 1
    assert svc.vehicles.created  # vehicle was created


def test_entry_known_vehicle_creates_new_session_when_no_active(monkeypatch):
    _patch_barrier(monkeypatch)

    svc = gate_module.GateService(FakeDB())
    svc.vehicles = FakeVehicleRepo(vehicle=FakeVehicle(id=5, is_blacklisted=False))
    svc.sessions = FakeSessionRepo(active=None)
    svc.drivers = FakeDriverRepo()
    svc.subs = FakeSubsRepo()
    svc.plans = FakePlanRepo()

    out = svc.handle_entry_scan(region_code="CA", plate_text="1234AB", gate_id="1", source="camera")

    assert out["reason"] == "created"
    assert out["session_id"] == 1
    assert svc.sessions.created
    assert svc.sessions.created[0][0] == 5  # vehicle_id used


def test_entry_unknown_vehicle_denied_when_visitor_mode_off(monkeypatch):
    _patch_barrier(monkeypatch)
    monkeypatch.setattr(gate_module, "VISITOR_MODE_ENABLED", False)

    svc = gate_module.GateService(FakeDB())
    svc.vehicles = FakeVehicleRepo(vehicle=None)
    svc.sessions = FakeSessionRepo(active=None)
    svc.drivers = FakeDriverRepo()
    svc.subs = FakeSubsRepo()
    svc.plans = FakePlanRepo()

    with pytest.raises(HTTPException) as e:
        svc.handle_entry_scan(region_code="XX", plate_text="NOPE", gate_id="1", source="camera")

    assert e.value.status_code == 403
    assert e.value.detail == "not_allowed"


def test_exit_unknown_vehicle_holds(monkeypatch):
    _patch_barrier(monkeypatch)

    svc = gate_module.GateService(FakeDB())
    svc.vehicles = FakeVehicleRepo(vehicle=None)  # not found
    svc.sessions = FakeSessionRepo(active=None)
    svc.drivers = FakeDriverRepo()
    svc.subs = FakeSubsRepo()
    svc.plans = FakePlanRepo()

    out = svc.handle_exit_scan(region_code="BG", plate_text="UNKNOWN", gate_id="2", source="camera")

    assert out["status"] == "error"
    assert out["barrier_action"] == "hold"
    assert out["detail"] == "vehicle_not_found"
    assert out["session_id"] is None


def test_exit_already_closed_session_is_idempotent(monkeypatch):
    _patch_barrier(monkeypatch)

    v = FakeVehicle(id=3)
    closed = FakeSession(id=22, ended_at=datetime.now(timezone.utc))

    svc = gate_module.GateService(FakeDB())
    svc.vehicles = FakeVehicleRepo(vehicle=v)
    svc.sessions = FakeSessionRepo(active=closed)
    svc.drivers = FakeDriverRepo()
    svc.subs = FakeSubsRepo(active_sub=False)
    svc.plans = FakePlanRepo()

    out = svc.handle_exit_scan(region_code="BG", plate_text="ABC", gate_id="2", source="camera")

    assert out["status"] == "closed"
    assert out["detail"] == "already_closed"
    assert out["barrier_action"] == "open"
    assert out["session_id"] == 22


def test_exit_subscriber_closes_session_and_opens(monkeypatch):
    _patch_barrier(monkeypatch)

    v = FakeVehicle(id=3, is_blacklisted=False)
    active_session = FakeSession(id=11, ended_at=None)

    svc = gate_module.GateService(FakeDB())
    svc.vehicles = FakeVehicleRepo(vehicle=v)
    svc.sessions = FakeSessionRepo(active=active_session)
    svc.drivers = FakeDriverRepo()
    svc.subs = FakeSubsRepo(active_sub=True)
    svc.plans = FakePlanRepo()

    out = svc.handle_exit_scan(region_code="BG", plate_text="ABC", gate_id="2", source="camera")

    assert out["status"] == "closed"
    assert out["detail"] == "subscriber_exit"
    assert out["barrier_action"] == "open"
    assert out["session_id"] == 11
    assert svc.sessions.ended  # end_session called


def test_exit_visitor_requires_payment(monkeypatch):
    _patch_barrier(monkeypatch)

    # make pricing deterministic
    monkeypatch.setattr(gate_module, "compute_amount_cents", lambda *a, **k: (120, 12))

    v = FakeVehicle(id=3)
    active = FakeSession(id=30, ended_at=None)
    active.started_at = datetime(2025, 1, 1, tzinfo=timezone.utc)

    svc = gate_module.GateService(FakeDB())
    svc.vehicles = FakeVehicleRepo(vehicle=v)
    svc.sessions = FakeSessionRepo(active=active)
    svc.drivers = FakeDriverRepo()
    svc.subs = FakeSubsRepo(active_sub=False)
    svc.plans = FakePlanRepo(visitor_plan=FakeVisitorPlan(id=9))

    out = svc.handle_exit_scan(region_code="BG", plate_text="ABC", gate_id="2", source="camera")

    assert out["status"] == "awaiting_payment"
    assert out["barrier_action"] == "hold"
    assert out["detail"] == "visitor_exit_payment_required"
    assert out["amount_cents"] == 120
    assert out["minutes_billable"] == 12
    assert out["plan_id"] == 9
