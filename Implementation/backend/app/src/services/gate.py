# backend/app/src/services/gate.py
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session
import requests

from .pricing import compute_amount_cents
from ..core.settings import settings
from ..repositories.plan_sqlalchemy import PlanRepository
from ..repositories.session_sqlalchemy import ParkingSessionRepository
from ..repositories.vehicle_sqlalchemy import VehicleRepository
from ..repositories.driver_sqlalchemy import DriverRepository  # uses helpers below
from ..repositories.subscription_sqlalchemy import SubscriptionRepository


# Toggle: auto-register unknown plates as "Visitor"
VISITOR_MODE_ENABLED = True
VISITOR_DRIVER_EMAIL = "visitor@system.local"
VISITOR_DRIVER_NAME = "Visitor"

IDEMPOTENCY_WINDOW = timedelta(minutes=5)


def _barrier_pulse_open(seconds: int = 5):
    """
    Ask the Raspberry Pi LED server to pulse green (open) for N seconds,
    then it will go back to red (closed).
    If BARRIER_PI_BASE_URL is not configured, this is a no-op.
    """
    base = getattr(settings, "BARRIER_PI_BASE_URL", None)
    if not base:
        return

    base = base.rstrip("/")
    try:
        requests.post(
            f"{base}/led/pulse",
            json={"seconds": seconds},
            timeout=0.5,
        )
    except Exception as e:
        print(f"[BARRIER] Failed to pulse open: {e}")


def _barrier_force_close():
    """
    Force the barrier into CLOSED state (red on).
    If BARRIER_PI_BASE_URL is not configured, this is a no-op.
    """
    base = getattr(settings, "BARRIER_PI_BASE_URL", None)
    if not base:
        return

    base = base.rstrip("/")
    try:
        requests.post(
            f"{base}/led/close",
            timeout=0.5,
        )
    except Exception as e:
        print(f"[BARRIER] Failed to force close: {e}")


class GateService:
    def __init__(self, db: Session):
        self.db = db
        self.sessions = ParkingSessionRepository(db)
        self.vehicles = VehicleRepository(db)
        self.drivers = DriverRepository(db)
        self.subs = SubscriptionRepository(db)
        self.plans = PlanRepository(db)

    def _ensure_visitor_driver(self):
        d = self.drivers.get_by_email(VISITOR_MODE_ENABLED and VISITOR_DRIVER_EMAIL)
        if d:
            return d
        return self.drivers.create(name=VISITOR_DRIVER_NAME, email=VISITOR_DRIVER_EMAIL)

    def handle_entry_scan(
        self,
        *,
        region_code: str,
        plate_text: str,
        gate_id: str | None,
        source: str | None,
    ):
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
            _barrier_force_close()
            raise HTTPException(status_code=403, detail="blacklisted")

        # 3) Idempotency: if there's any OPEN session, reuse it
        active = self.sessions.get_active_for_vehicle(vehicle.id)
        if active:
            # Barrier should open (same as before: barrier_action="open")
            _barrier_pulse_open(seconds=5)
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

        # Ask the Pi to open the barrier (green for N seconds then red)
        _barrier_pulse_open(seconds=5)

        return {
            "status": "open",
            "reason": "created",
            "session_id": new_sess.id,
            "barrier_action": "open",
            "created_at_utc": new_sess.started_at,
        }

    def handle_exit_scan(
        self,
        *,
        region_code: str,
        plate_text: str,
        gate_id: str | None,
        source: str | None,
    ):
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
            _barrier_force_close()
            return {
                "session_id": None,
                "status": "error",
                "barrier_action": "hold",
                "detail": "vehicle_not_found",
            }

        s = self.sessions.get_active_for_vehicle(vehicle.id)
        if not s:
            # Idempotency for visitors: if a recent exit already priced this session,
            # return the same quote instead of failing.
            awaiting = self.sessions.get_latest_awaiting_payment_for_vehicle(vehicle.id)
            if awaiting:
                _barrier_force_close()
                return {
                    "session_id": awaiting.id,
                    "status": "awaiting_payment",
                    "barrier_action": "hold",
                    "detail": "visitor_exit_payment_required",
                    "amount_cents": awaiting.amount_charged,
                    "currency": awaiting.plan.currency if getattr(awaiting, "plan", None) else None,
                    "minutes_billable": awaiting.duration,
                    "plan_id": awaiting.plan_id,
                }

            # nothing open or awaiting -> still invalid order
            _barrier_force_close()
            return {
                "session_id": None,
                "status": "error",
                "barrier_action": "hold",
                "detail": "no_open_session_for_vehicle",
            }

        # Idempotency: if a race already ended it
        if s.ended_at is not None:
            # This branch says barrier_action="open" (idempotent open)
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
            # Existing behavior: barrier_action="open".
            # We can leave actual Pi pulse to the payment/exit flow if you prefer.
            return {
                "session_id": s.id,
                "status": "closed",
                "barrier_action": "open",
                "detail": "subscriber_exit",
            }

        # ---------- Visitor branch ----------
        # Idempotency: if already priced & awaiting payment, re-use same quote
        if getattr(s, "status", None) == "awaiting_payment" and s.amount_charged is not None:
            _barrier_force_close()
            return {
                "session_id": s.id,
                "status": "awaiting_payment",
                "barrier_action": "hold",
                "detail": "visitor_exit_payment_required",
                "amount_cents": s.amount_charged,
                "currency": s.plan.currency if s.plan else None,
                "minutes_billable": s.duration,
                "plan_id": s.plan_id,
            }

        vplan = self.plans.get_default_visitor_plan()
        if not vplan or vplan.price_per_minute_cents is None:
            _barrier_force_close()
            return {
                "session_id": s.id,
                "status": "error",
                "barrier_action": "hold",
                "detail": "visitor_plan_not_configured",
            }

        amount_cents, minutes = compute_amount_cents(
            s.started_at,
            now,
            vplan.price_per_minute_cents,
            settings.PRICING_GRACE_MINUTES,
            settings.PRICING_ROUND_UP,
        )

        # write RM fields
        s.plan_id = vplan.id
        s.ended_at = now
        s.duration = minutes
        s.amount_charged = amount_cents

        if settings.GRACE_AUTOCLOSE_ENABLED and amount_cents == 0:
            s.status = "closed"
            self.db.commit()
            self.db.refresh(s)
            # barrier_action="open" (free exit)
            return {
                "session_id": s.id,
                "status": "closed",
                "barrier_action": "open",
                "detail": "grace_exit_free",
            }

        s.status = "awaiting_payment"
        self.db.commit()
        self.db.refresh(s)

        _barrier_force_close()
        return {
            "session_id": s.id,
            "status": "awaiting_payment",
            "barrier_action": "hold",
            "detail": "visitor_exit_payment_required",
            "amount_cents": s.amount_charged,
            "currency": vplan.currency,
            "minutes_billable": minutes,
            "plan_id": vplan.id,
        }
