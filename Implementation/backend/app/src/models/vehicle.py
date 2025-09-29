from sqlalchemy import Column, Integer, String, ForeignKey, Index
from sqlalchemy.orm import relationship
from .base import Base

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False)
    region_code = Column(String(10), nullable=False)
    plate_text = Column(String(16), nullable=False)

    driver = relationship("Driver", back_populates="vehicles")
    sessions = relationship("Session", back_populates="vehicle", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="vehicle", cascade="all, delete-orphan")

# Fast lookup on plates
Index("ix_vehicles_plate_unique", Vehicle.region_code, Vehicle.plate_text, unique=True)
