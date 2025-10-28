# backend/app/src/repositories/admin_sqlalchemy.py
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from datetime import datetime, timedelta, timezone
import secrets
from ..models.admin import Admin, AdminRole, AdminStatus

class AdminRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, *, name: str, email: str, password_hash: str,
               verified: bool = False, is_accountant: bool = False) -> Admin:
        obj = Admin(
            name=name,
            email=email,
            password=password_hash,
            verified=verified,
            is_accountant=is_accountant,
        )
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get(self, admin_id: int) -> Admin | None:
        return self.db.get(Admin, admin_id)

    def get_by_email(self, email: str) -> Admin | None:
        return self.db.execute(select(Admin).where(Admin.email == email)).scalar_one_or_none()

    def list(self, *, skip: int = 0, limit: int = 50) -> list[Admin]:
        return self.db.execute(select(Admin).offset(skip).limit(limit)).scalars().all()

    def update(self, admin: Admin, **fields) -> Admin:
        for k, v in fields.items():
            if v is not None:
                setattr(admin, k, v)
        self.db.commit()
        self.db.refresh(admin)
        return admin

    def delete(self, admin: Admin) -> None:
        self.db.delete(admin)
        self.db.commit()

    def create_invited(self, *, email: str, role: AdminRole, invited_by_id: int, name: str | None, expires_minutes: int) -> Admin:
        token = secrets.token_urlsafe(48)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
        admin = Admin(
            name=name or email.split("@")[0],
            email=email,
            password="!",  # placeholder; will be set on accept
            role=role,
            status=AdminStatus.invited,
            is_active=False,
            invited_token=token,
            invited_expires_at=expires_at,
            invited_by_id=invited_by_id,
        )
        self.db.add(admin)
        self.db.commit()
        self.db.refresh(admin)
        return admin

    def get_by_invited_token(self, token: str) -> Admin | None:
        return self.db.execute(select(Admin).where(Admin.invited_token == token)).scalar_one_or_none()

    def activate_from_invite(self, admin: Admin, password_hash: str, name: str | None = None) -> Admin:
        admin.password = password_hash
        if name:
            admin.name = name
        admin.status = AdminStatus.active
        admin.is_active = True
        admin.invited_token = None
        admin.invited_expires_at = None
        self.db.commit()
        self.db.refresh(admin)
        return admin

    def deactivate(self, admin: Admin) -> Admin:
        admin.status = AdminStatus.disabled
        admin.is_active = False
        self.db.commit()
        self.db.refresh(admin)
        return admin

    def reactivate(self, admin: Admin) -> Admin:
        admin.status = AdminStatus.active
        admin.is_active = True
        self.db.commit()
        self.db.refresh(admin)
        return admin

    def count_owners(self) -> int:
        return self.db.execute(
            select(func.count()).select_from(Admin)
            .where(Admin.role == AdminRole.owner, Admin.is_active == True)
        ).scalar_one()

    # --- guardrails helpers ---
    def assert_can_manage(self, actor: Admin, target: Admin, new_role: AdminRole | None = None):
        if actor.id == target.id:
            raise PermissionError("You cannot modify your own account.")
        if target.role == AdminRole.owner and actor.role != AdminRole.owner:
            raise PermissionError("Only owners can manage owners.")
        if new_role == AdminRole.owner and actor.role != AdminRole.owner:
            raise PermissionError("Only owners can assign owner role.")
        # protect last owner
        if target.role == AdminRole.owner and self.count_owners() <= 1:
            raise PermissionError("Cannot modify or disable the last owner.")