from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models.vehicle import Vehicle
from ..models.plan import Plan, PlanType
from ..models.subscription import Subscription
from ..repositories.subscription_sqlalchemy import SubscriptionRepository

class SubscriptionService:
    def __init__(self, repo: SubscriptionRepository):
        self.repo = repo
        self.db: Session = repo.db  # reuse the session held by the repo

    def _ensure_refs(self, vehicle_id: int, plan_id: int) -> Plan:
        if self.db.get(Vehicle, vehicle_id) is None:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        plan = self.db.get(Plan, plan_id)
        if plan is None:
            raise HTTPException(status_code=404, detail="Plan not found")
        if plan.type != PlanType.subscription:
            raise HTTPException(status_code=400, detail="Plan is not a subscription plan")
        return plan

    def _validate_range(self, start: datetime, end: datetime) -> None:
        if start >= end:
            raise HTTPException(status_code=400, detail="valid_from must be before valid_to")

    def create(
        self,
        *,
        vehicle_id: int,
        plan_id: int,
        valid_from: datetime,
        valid_to: datetime,
        auto_renew: bool = True,
    ) -> Subscription:
        self._ensure_refs(vehicle_id, plan_id)
        self._validate_range(valid_from, valid_to)

        # Still block overlaps with existing *active* subs
        if self.repo.has_overlapping_active(vehicle_id, valid_from, valid_to):
            raise HTTPException(status_code=409, detail="Overlapping active subscription exists")

        # Admin creates (this is the “approval”) → starts as pending_payment
        return self.repo.create(
            vehicle_id=vehicle_id,
            plan_id=plan_id,
            status="pending_payment",
            auto_renew=auto_renew,
            valid_from=valid_from,
            valid_to=valid_to,
        )

    def get(self, sub_id: int) -> Subscription:
        sub = self.repo.get(sub_id)
        if not sub:
            raise HTTPException(status_code=404, detail="Subscription not found")
        return sub

    def list_for_vehicle(self, vehicle_id: int) -> list[Subscription]:
        return self.repo.list_by_vehicle(vehicle_id)

    def _ensure_payment_then_activate(self, sub: Subscription) -> Subscription:
        if not self.repo.has_successful_payment(sub.id):
            raise HTTPException(status_code=409, detail="No successful payment for this subscription")

        # Optional: sanity on time window
        now = datetime.now(timezone.utc)
        if sub.valid_to <= now:
            raise HTTPException(status_code=400, detail="Subscription validity window has already ended")

        # Activate
        return self.repo.update_status(sub, status="active", auto_renew=None)

    def set_status(self, sub_id: int, *, status: str, auto_renew: bool | None) -> Subscription:
        sub = self.get(sub_id)

        # Guard rails: can’t force 'active' without a succeeded payment
        if status == "active":
            return self._ensure_payment_then_activate(sub)

        # Allow pausing/canceling regardless of payment (normal ops)
        if status in {"paused", "canceled"}:
            return self.repo.update_status(sub, status=status, auto_renew=auto_renew)

        # Don’t let external callers push it back to pending_payment
        if status == "pending_payment":
            raise HTTPException(status_code=400, detail="Status transition not allowed")

        raise HTTPException(status_code=400, detail="Unsupported status value")

    def activate_on_payment(self, sub_id: int) -> Subscription:
        """Call this from a payment webhook / payments router after marking the Payment as succeeded."""
        sub = self.get(sub_id)
        return self._ensure_payment_then_activate(sub)

    def delete(self, sub_id: int) -> None:
        sub = self.get(sub_id)
        self.repo.delete(sub)
