from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)  # active until set
    # It can be computed on the fly the duration

    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="RESTRICT"), nullable=True)
    status = Column(String(24), nullable=True)  # "open" | "awaiting_payment" | "closed"
    duration = Column(Integer, nullable=True)  # minutes
    amount_charged = Column(Integer, nullable=True)  # cents

    vehicle = relationship("Vehicle", back_populates="sessions")
    payments = relationship("Payment", back_populates="session", cascade="all, delete-orphan")

    plan = relationship("Plan", back_populates="sessions", lazy="joined")
