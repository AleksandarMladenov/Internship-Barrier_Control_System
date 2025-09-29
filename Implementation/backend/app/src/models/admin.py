from sqlalchemy import Boolean, Column, Integer, String
from .base import Base

class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    verified = Column(Boolean, nullable=False, default=False)
    is_accountant = Column(Boolean, nullable=False, default=False)
