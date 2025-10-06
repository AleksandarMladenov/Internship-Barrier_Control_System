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
