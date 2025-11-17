from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=True)

    status = Column(String(32), nullable=False, default="pending")
    currency = Column(String(3), nullable=False)
    amount_cents = Column(Integer, nullable=False)
    method = Column(String(32), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    stripe_checkout_id = Column(String(255), nullable=True, index=True)
    stripe_payment_intent_id = Column(String(64), nullable=True, index=True)

    session = relationship("Session", back_populates="payments")
    subscription = relationship("Subscription")
