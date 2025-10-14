import stripe
from fastapi import HTTPException
from sqlalchemy.orm import Session as SASession
from typing import Optional

from ..core import settings
from ..repositories.payment_sqlalchemy import PaymentRepository
from ..models.payment import Payment
from ..models.session import Session as SessionModel
from ..models.subscription import Subscription
from ..models.plan import Plan
from ..repositories.plan_sqlalchemy import PlanRepository
from ..repositories.session_sqlalchemy import ParkingSessionRepository
from ..schemas.payment import PaymentCreate, PaymentUpdateStatus, PaymentStatus

# Reuse your subscription activation logic
from ..repositories.subscription_sqlalchemy import SubscriptionRepository
from ..services.subscriptions import SubscriptionService

class PaymentService:
    """
    Rules:
    - Exactly one of session_id or subscription_id must be provided (enforced at schema and rechecked).
    - On success:
        * if subscription_id is set → attempt to activate that subscription (pending_payment → active).
    - On refund/fail: no subscription activation.
    - Optional guard: block deleting succeeded payments (prefer refund).
    """
    def __init__(self, repo: PaymentRepository):
        self.repo = repo
        self.db: SASession = repo.db

    def _ensure_refs(self, session_id: Optional[int], subscription_id: Optional[int]) -> None:
        if bool(session_id) == bool(subscription_id):
            raise HTTPException(status_code=400, detail="Provide exactly one of session_id or subscription_id")
        if session_id is not None and self.db.get(SessionModel, session_id) is None:
            raise HTTPException(status_code=404, detail="Session not found")
        if subscription_id is not None and self.db.get(Subscription, subscription_id) is None:
            raise HTTPException(status_code=404, detail="Subscription not found")

    def create(self, payload: PaymentCreate) -> Payment:
        data = payload.model_dump()
        # uppercase already handled in schema; re-normalize for safety
        data["currency"] = data["currency"].upper()

        self._ensure_refs(data.get("session_id"), data.get("subscription_id"))
        return self.repo.create(**data)

    def get(self, payment_id: int) -> Payment:
        p = self.repo.get(payment_id)
        if not p:
            raise HTTPException(status_code=404, detail="Payment not found")
        return p

    def list(
        self,
        *,
        session_id: Optional[int],
        subscription_id: Optional[int],
        status: Optional[PaymentStatus],
    ) -> list[Payment]:
        status_str = status.value if status else None
        return self.repo.list(session_id=session_id, subscription_id=subscription_id, status=status_str)

    def _activate_subscription_if_needed(self, p: Payment) -> None:
        if p.subscription_id is None:
            return
        # Activate only if payment succeeded
        if p.status != "succeeded":
            return

        sub_repo = SubscriptionRepository(self.db)
        sub_svc = SubscriptionService(sub_repo)
        sub_svc.activate_on_payment(p.subscription_id)

    def set_status(self, payment_id: int, new_status: PaymentStatus) -> Payment:
        p = self.get(payment_id)

        # idempotency-ish: if already at target, return
        if p.status == new_status.value:
            return p

        # Allowed transitions from pending: succeeded | failed
        if p.status == "pending":
            if new_status not in {PaymentStatus.succeeded, PaymentStatus.failed}:
                raise HTTPException(status_code=400, detail="Only succeeded or failed allowed from pending")
        # From succeeded: only refunded allowed
        elif p.status == "succeeded":
            if new_status != PaymentStatus.refunded:
                raise HTTPException(status_code=400, detail="Only refunded allowed from succeeded")
        # From failed: allow no further transitions
        elif p.status == "failed":
            raise HTTPException(status_code=400, detail="No transitions allowed from failed")
        # From refunded: no further transitions
        elif p.status == "refunded":
            raise HTTPException(status_code=400, detail="No transitions allowed from refunded")

        p = self.repo.set_status(p, new_status.value)

        # Side effect: activation on success for subscriptions
        if new_status == PaymentStatus.succeeded:
            self._activate_subscription_if_needed(p)

        return p

    def delete(self, payment_id: int) -> None:
        p = self.get(payment_id)
        # Optional guard: block deleting succeeded payments (prefer refund)
        if p.status == "succeeded":
            raise HTTPException(status_code=409, detail="Cannot delete succeeded payment; refund instead")
        self.repo.delete(p)

        def _session_repo(self) -> ParkingSessionRepository:
            return ParkingSessionRepository(self.db)

        def _plan_repo(self) -> PlanRepository:
            return PlanRepository(self.db)

        def create_checkout_for_session(self, session_id: int) -> dict:
            sessions = self._session_repo()
            s = sessions.get(session_id)
            if not s:
                raise HTTPException(status_code=404, detail="session_not_found")

            if getattr(s, "status", None) not in (None, "awaiting_payment"):
                raise HTTPException(status_code=409, detail="session_not_payable")

            if not s.amount_charged or s.amount_charged <= 0 or not s.plan:
                raise HTTPException(status_code=400, detail="invalid_amount_or_plan")

            # return same pending payment if exists
            existing = self.repo.get_pending_for_session(session_id)
            if existing and existing.stripe_checkout_id:
                return {"checkout_url": f"https://checkout.stripe.com/c/pay/{existing.stripe_checkout_id}"}

            # create pending payment row
            p = self.repo.create(
                session_id=session_id,
                subscription_id=None,
                status="pending",
                currency=(s.plan.currency or "EUR").upper(),
                amount_cents=int(s.amount_charged),
                method="card",
            )

            try:
                cs = stripe.checkout.Session.create(
                    mode="payment",
                    currency=p.currency.lower(),
                    line_items=[{
                        "price_data": {
                            "currency": p.currency.lower(),
                            "unit_amount": p.amount_cents,
                            "product_data": {"name": f"Parking session #{s.id}"},
                        },
                        "quantity": 1,
                    }],
                    payment_intent_data={"metadata": {"session_id": s.id, "payment_id": p.id}},
                    metadata={"session_id": s.id, "payment_id": p.id},
                    success_url=f"{settings.PUBLIC_BASE_URL}/payments/success?session_id={s.id}",
                    cancel_url=f"{settings.PUBLIC_BASE_URL}/payments/cancel?session_id={s.id}",
                )
            except stripe.error.StripeError:
                raise HTTPException(status_code=502, detail="stripe_error")

            self.repo.attach_stripe_ids(
                p,
                checkout_id=cs.get("id"),
                payment_intent_id=cs.get("payment_intent"),
            )
            return {"checkout_url": cs.get("url")}
