# backend/app/src/services/admins.py

from typing import Optional, List

from ..core.security import hash_password
from ..repositories.admin_sqlalchemy import AdminRepository
from ..models.admin import Admin, AdminRole, AdminStatus


class AdminService:
    def __init__(self, repo: AdminRepository):
        self.repo = repo

    # helper
    def _hash(self, raw: str) -> str:
        return hash_password(raw)

    # CREATE (Owner only)
    def create(
        self,
        *,
        name: str,
        email: str,
        password: str,
        role: AdminRole = AdminRole.viewer,
        is_active: bool = True,
    ) -> Admin:
        if self.repo.get_by_email(email):
            raise ValueError("Email already in use")

        password_hash = self._hash(password)

        return self.repo.create(
            name=name,
            email=email,
            password_hash=password_hash,
            role=role,
            is_active=is_active,
        )

    # READ single
    def get(self, admin_id: int) -> Optional[Admin]:
        return self.repo.get(admin_id)

    # LIST
    def list(self, *, skip: int = 0, limit: int = 50) -> List[Admin]:
        return self.repo.list(skip=skip, limit=limit)

    # UPDATE (Owner only)
    def update(
        self,
        admin_id: int,
        *,
        name: Optional[str] = None,
        password: Optional[str] = None,
        role: Optional[AdminRole] = None,
        is_active: Optional[bool] = None,
        status: Optional[AdminStatus] = None,
    ) -> Admin:
        admin = self.repo.get(admin_id)
        if not admin:
            raise LookupError("Admin not found")

        fields = {}
        if name is not None:
            fields["name"] = name
        if role is not None:
            fields["role"] = role
        if is_active is not None:
            fields["is_active"] = is_active
        if status is not None:
            fields["status"] = status

        if password:
            fields["password"] = self._hash(password)

        return self.repo.update(admin, **fields)

    # DELETE (soft-delete enforced)
    def delete(self, admin_id: int) -> None:
        admin = self.repo.get(admin_id)
        if not admin:
            raise LookupError("Admin not found")
        self.repo.deactivate(admin)
