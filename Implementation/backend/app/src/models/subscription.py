from sqlalchemy import Column, Integer, ForeignKey, Boolean, DateTime, String
from sqlalchemy.orm import relationship
from .base import Base

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False)

    status = Column(String(32), nullable=False, default="active")  # "active", "paused", "canceled"
    auto_renew = Column(Boolean, nullable=False, default=True)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True), nullable=False)

    vehicle = relationship("Vehicle", back_populates="subscriptions")
    plan = relationship("Plan")
