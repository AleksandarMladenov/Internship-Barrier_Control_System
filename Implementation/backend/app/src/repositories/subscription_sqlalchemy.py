from datetime import datetime, timezone
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_

from .session_sqlalchemy import ParkingSessionRepository
from ..models import Vehicle
from ..models.subscription import Subscription
from ..models.payment import Payment  # 👈 import payment model
from ..models.plan import Plan, PlanType

class SubscriptionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs) -> Subscription:
        sub = Subscription(**kwargs)
        self.db.add(sub)
        self.db.commit()
        self.db.refresh(sub)
        return sub

    def get(self, sub_id: int) -> Subscription | None:
        return self.db.get(Subscription, sub_id)

    def list_by_vehicle(self, vehicle_id: int) -> list[Subscription]:
        return (
            self.db.query(Subscription)
            .filter(Subscription.vehicle_id == vehicle_id)
            .order_by(Subscription.id.desc())
            .all()
        )

    def has_overlapping_active(self, vehicle_id: int, start: datetime, end: datetime) -> bool:
        q = (
            self.db.query(Subscription)
            .filter(
                Subscription.vehicle_id == vehicle_id,
                Subscription.status == "active",
                or_(
                    and_(Subscription.valid_from <= start, Subscription.valid_to > start),
                    and_(Subscription.valid_from < end,   Subscription.valid_to >= end),
                    and_(Subscription.valid_from >= start, Subscription.valid_to <= end),
                ),
            )
        )
        return self.db.query(q.exists()).scalar()  # type: ignore

    def has_successful_payment(self, sub_id: int) -> bool:
        q = (
            self.db.query(Payment)
            .filter(Payment.subscription_id == sub_id, Payment.status == "succeeded")
        )
        return self.db.query(q.exists()).scalar()  # type: ignore

    def update_status(self, sub: Subscription, *, status: str, auto_renew: bool | None) -> Subscription:
        sub.status = status
        if auto_renew is not None:
            sub.auto_renew = auto_renew
        self.db.commit()
        self.db.refresh(sub)
        return sub

    def delete(self, sub: Subscription) -> None:
        self.db.delete(sub)
        self.db.commit()

    def get_active_subscription_plan_for_vehicle_at(
                self, vehicle_id: int, at_ts: datetime
        ) -> Subscription | None:
            """
            Return an active subscription for the vehicle at 'at_ts'
            whose linked plan.type == 'subscription'.
            """
            return (
                self.db.query(Subscription)
                .join(Plan, Plan.id == Subscription.plan_id)
                .options(joinedload(Subscription.plan))
                .filter(
                    Subscription.vehicle_id == vehicle_id,
                    Subscription.status == "active",
                    Subscription.valid_from <= at_ts,
                    Subscription.valid_to > at_ts,
                    Plan.type == PlanType.subscription,
                )
                .order_by(Subscription.valid_to.desc())
                .first()
     )
    def suspend_all_for_vehicle(self, vehicle_id: int) -> int:
        """Set status='suspended' for currently active subscriptions within validity window."""
        now = datetime.utcnow()
        q = (
            self.db.query(Subscription)
            .filter(
                Subscription.vehicle_id == vehicle_id,
                Subscription.status == "active",
                Subscription.valid_from <= now,
                Subscription.valid_to > now,
            )
        )
        updated = q.update({Subscription.status: "suspended"}, synchronize_session=False)
        self.db.commit()
        return int(updated)

    def resume_all_for_vehicle(self, vehicle_id: int) -> int:

        now = datetime.utcnow()
        q = (
            self.db.query(Subscription)
            .filter(
                Subscription.vehicle_id == vehicle_id,
                Subscription.status == "suspended",
                Subscription.valid_from <= now,
                Subscription.valid_to > now,
            )
        )
        updated = q.update({Subscription.status: "active"}, synchronize_session=False)
        self.db.commit()
        return int(updated)


    def delete_if_blacklisted(self, vehicle_id: int) -> bool:
        v = self.db.get(Vehicle, vehicle_id)
        if not v or not v.is_blacklisted:
            return False

        try:
            sessions = ParkingSessionRepository(self.db)
            active = sessions.get_active_for_vehicle(v.id)
            if active:
                sessions.end_session(active)
        except Exception:
            pass
        self.db.delete(v)
        self.db.commit()
        return True

    def cancel_all_active_for_vehicle(self, vehicle_id: int) -> int:
        """
        Hard-stop any currently active subscription rows:
        - set valid_to = now (UTC)
        - set auto_renew = False
        - set status = 'canceled'
        """
        now = datetime.now(timezone.utc)
        q = (
            self.db.query(Subscription)
            .filter(
                Subscription.vehicle_id == vehicle_id,
                Subscription.status.in_(["active", "suspended"]),  # be defensive
                Subscription.valid_from <= now,
                Subscription.valid_to > now,
            )
        )
        updated = q.update(
            {
                Subscription.valid_to: now,
                Subscription.auto_renew: False,
                Subscription.status: "canceled",
            },
            synchronize_session=False,
        )
        self.db.commit()
        return int(updated)

    def has_active_now(self, vehicle_id: int) -> bool:
        """
        True if the vehicle currently has an active subscription (now falls in window).
        """
        now = datetime.now(timezone.utc)
        q = (
            self.db.query(Subscription)
            .filter(
                Subscription.vehicle_id == vehicle_id,
                Subscription.status == "active",
                Subscription.valid_from <= now,
                Subscription.valid_to > now,
            )
        )
        return bool(self.db.query(q.exists()).scalar())
