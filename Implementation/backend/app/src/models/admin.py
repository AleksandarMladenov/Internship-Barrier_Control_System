# backend/app/src/models/admin.py
from sqlalchemy import Boolean, Column, Integer, String, DateTime, func, Enum as SAEnum
from .base import Base
import enum

class AdminRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    viewer = "viewer"

class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)

    role = Column(SAEnum(AdminRole, name="admin_role"), nullable=False, index=True, default=AdminRole.viewer)
    is_active = Column(Boolean, nullable=False, default=True)

    verified = Column(Boolean, nullable=False, default=False)
    is_accountant = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)
