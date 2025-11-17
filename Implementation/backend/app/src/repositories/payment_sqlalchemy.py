# backend/app/src/repositories/payment_sqlalchemy.py
from typing import Optional, List
from sqlalchemy.orm import Session
from ..models.payment import Payment

class PaymentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs) -> Payment:
        p = Payment(**kwargs)
        self.db.add(p)
        self.db.commit()
        self.db.refresh(p)
        return p

    def get(self, payment_id: int) -> Optional[Payment]:
        return self.db.get(Payment, payment_id)

    def list(
        self,
        *,
        session_id: Optional[int] = None,
        subscription_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> List[Payment]:
        q = self.db.query(Payment)
        if session_id is not None:
            q = q.filter(Payment.session_id == session_id)
        if subscription_id is not None:
            q = q.filter(Payment.subscription_id == subscription_id)
        if status is not None:
            q = q.filter(Payment.status == status)
        return q.order_by(Payment.id.desc()).all()

    def set_status(self, p: Payment, status: str) -> Payment:
        p.status = status
        self.db.commit()
        self.db.refresh(p)
        return p

    def delete(self, p: Payment) -> None:
        self.db.delete(p)
        self.db.commit()

    # ---------- helpers you need ----------
    def get_pending_for_session(self, session_id: int) -> Optional[Payment]:
        return (
            self.db.query(Payment)
            .filter(Payment.session_id == session_id, Payment.status == "pending")
            .order_by(Payment.id.desc())
            .first()
        )

    def attach_stripe_ids(self, p: Payment, *, checkout_id: Optional[str], payment_intent_id: Optional[str]):
        if checkout_id:
            p.stripe_checkout_id = checkout_id
        if payment_intent_id:
            p.stripe_payment_intent_id = payment_intent_id
        self.db.commit()
        self.db.refresh(p)
        return p

    def set_checkout_session_id(self, payment_id: int, checkout_id: str):
        p = self.get(payment_id)
        if not p:
            return
        p.stripe_checkout_id = checkout_id
        self.db.commit()
        self.db.refresh(p)
        return p

    def get_by_checkout_session_id(self, checkout_id: str) -> Optional[Payment]:
        return self.db.query(Payment).filter(Payment.stripe_checkout_id == checkout_id).first()

    def get_by_payment_intent(self, pi_id: str) -> Optional[Payment]:
        return self.db.query(Payment).filter(Payment.stripe_payment_intent_id == pi_id).first()
