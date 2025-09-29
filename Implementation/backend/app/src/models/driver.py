from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from .base import Base

class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)

    vehicles = relationship("Vehicle", back_populates="driver", cascade="all, delete-orphan")
