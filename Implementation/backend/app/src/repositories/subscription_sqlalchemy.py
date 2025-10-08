from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
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
