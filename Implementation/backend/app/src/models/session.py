from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)  # active until set
    # You can compute duration on the fly; no need to store seconds unless you want a snapshot

    vehicle = relationship("Vehicle", back_populates="sessions")
    payments = relationship("Payment", back_populates="session", cascade="all, delete-orphan")
