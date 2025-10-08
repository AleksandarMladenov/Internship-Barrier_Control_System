# backend/app/src/services/gate.py
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..repositories.session_sqlalchemy import ParkingSessionRepository
from ..repositories.vehicle_sqlalchemy import VehicleRepository
from ..repositories.driver_sqlalchemy import DriverRepository  # uses helpers below
from ..repositories.subscription_sqlalchemy import SubscriptionRepository


# Toggle: auto-register unknown plates as "Visitor"
VISITOR_MODE_ENABLED = True
VISITOR_DRIVER_EMAIL = "visitor@system.local"
VISITOR_DRIVER_NAME = "Visitor"

IDEMPOTENCY_WINDOW = timedelta(minutes=5)

class GateService:
    def __init__(self, db: Session):
        self.db = db
        self.sessions = ParkingSessionRepository(db)
        self.vehicles = VehicleRepository(db)
        self.drivers = DriverRepository(db)
        self.subs = SubscriptionRepository(db)

    def _ensure_visitor_driver(self):
        d = self.drivers.get_by_email(VISITOR_DRIVER_EMAIL)
        if d:
            return d
        return self.drivers.create(name=VISITOR_DRIVER_NAME, email=VISITOR_DRIVER_EMAIL)

    def handle_entry_scan(self, *, region_code: str, plate_text: str, gate_id: str | None, source: str | None):
        now = datetime.now(timezone.utc)
        region_code = region_code.strip().upper()
        plate_text = plate_text.strip().upper()

        # 1) Find or auto-register vehicle (if visitor mode is on)
        vehicle = self.vehicles.get_by_plate(region_code=region_code, plate_text=plate_text)
        if vehicle is not None:
            self.db.refresh(vehicle)  # ensure fresh values (is_blacklisted)

        if not vehicle:
            if not VISITOR_MODE_ENABLED:
                # Unknown plates disallowed when visitor mode is off
                raise HTTPException(status_code=403, detail="not_allowed")
            # Auto-register as a visitor vehicle
            visitor_driver = self._ensure_visitor_driver()
            vehicle = self.vehicles.create(
                driver_id=visitor_driver.id,
                region_code=region_code,
                plate_text=plate_text,
            )

        # 2) Blacklist check (you only have blacklist flag in RM – keep it simple)
        if getattr(vehicle, "is_blacklisted", False):
            # No session created, barrier stays closed
            raise HTTPException(status_code=403, detail="blacklisted")


        # 3) Idempotency: if there's any OPEN session, reuse it
        active = self.sessions.get_active_for_vehicle(vehicle.id)
        if active:
            return {
                "status": "open",
                "reason": "existing_open_session",
                "session_id": active.id,
                "barrier_action": "open",
                "created_at_utc": active.started_at,
            }

        # 4) Create new open session (ended_at NULL == open)
        new_sess = self.sessions.create(
            vehicle_id=vehicle.id,
            started_at=now,  # explicit UTC
        )

        return {
            "status": "open",
            "reason": "created",
            "session_id": new_sess.id,
            "barrier_action": "open",
            "created_at_utc": new_sess.started_at,
        }
    def handle_exit_scan(self, *, region_code: str, plate_text: str, gate_id: str | None, source: str | None):
        """
        Exit logic:
        - Find vehicle and its open session.
        - If already ended, return idempotent 'closed'/'open'.
        - If active subscription (plan.type == 'subscription') at NOW -> end session, open barrier.
        - Else -> visitor: hold barrier, await payment (Stripe story next).
        """
        now = datetime.now(timezone.utc)
        region_code = region_code.strip().upper()
        plate_text = plate_text.strip().upper()

        vehicle = self.vehicles.get_by_plate(region_code=region_code, plate_text=plate_text)
        if not vehicle:
            # Unknown vehicle at exit: hold (no session to close)
            return {
                "session_id": None,
                "status": "error",
                "barrier_action": "hold",
                "detail": "vehicle_not_found",
            }

        s = self.sessions.get_active_for_vehicle(vehicle.id)
        if not s:
            # Graceful invalid order: exit before entry
            return {
                "session_id": None,
                "status": "error",
                "barrier_action": "hold",
                "detail": "no_open_session_for_vehicle",
            }

        # Idempotency: if a race already ended it
        if s.ended_at is not None:
            return {
                "session_id": s.id,
                "status": "closed",
                "barrier_action": "open",
                "detail": "already_closed",
            }

        # Subscriber check at NOW
        active_sub = self.subs.get_active_subscription_plan_for_vehicle_at(vehicle.id, now)
        if active_sub:
            s = self.sessions.end_session(s, ended_at=now)
            return {
                "session_id": s.id,
                "status": "closed",
                "barrier_action": "open",
                "detail": "subscriber_exit",
            }

        # Visitor branch (Stripe comes next)
        return {
            "session_id": s.id,
            "status": "awaiting_payment",
            "barrier_action": "hold",
            "detail": "visitor_exit_payment_required",
        }

