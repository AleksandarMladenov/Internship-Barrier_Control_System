from typing import Optional, List
from passlib.hash import bcrypt
from ..core.security import hash_password

from ..repositories.admin_sqlalchemy import AdminRepository
from ..models.admin import Admin, AdminRole


class AdminService:
    def __init__(self, repo: AdminRepository):
        self.repo = repo

    # helper
    def _hash(self, raw: str) -> str:
        return hash_password(raw)
    def create(
        self,
        *,
        name: str,
        email: str,
        password: str,
        verified: bool = False,
        is_accountant: bool = False,
        role: AdminRole = AdminRole.viewer,
        is_active: bool = True,
    ) -> Admin:
        """
        Creates an admin. Your repository's create() accepts password_hash only,
        so we hash here and then (optionally) set role/is_active via update()
        to avoid changing the repo signature.
        """
        if self.repo.get_by_email(email):
            raise ValueError("Email already in use")

        admin = self.repo.create(
            name=name,
            email=email,
            password_hash=self._hash(password),
            verified=verified,
            is_accountant=is_accountant,
        )

        # Set role / is_active (if your repo.create doesn't take those fields)
        if (role is not None and admin.role != role) or (is_active is not None and admin.is_active != is_active):
            admin = self.repo.update(admin, role=role, is_active=is_active)

        return admin

    def get(self, admin_id: int) -> Optional[Admin]:
        return self.repo.get(admin_id)

    def list(self, *, skip: int = 0, limit: int = 50) -> List[Admin]:
        return self.repo.list(skip=skip, limit=limit)

    def update(
        self,
        admin_id: int,
        *,
        name: Optional[str] = None,
        verified: Optional[bool] = None,
        is_accountant: Optional[bool] = None,
        password: Optional[str] = None,
        role: Optional[AdminRole] = None,
        is_active: Optional[bool] = None,
    ) -> Admin:
        """
        Update uses repo.update() which sets attributes directly on the model,
        so use key 'password' (hashed), not 'password_hash'.
        """
        admin = self.repo.get(admin_id)
        if not admin:
            raise LookupError("Admin not found")

        fields = {
            "name":      name,
            "verified":  verified,
            "is_accountant": is_accountant,
            "role":      role,
            "is_active": is_active,
        }
        if password:
            fields["password"] = self._hash(password)  # <-- important: model column is 'password'

        return self.repo.update(admin, **fields)

    def delete(self, admin_id: int) -> None:
        admin = self.repo.get(admin_id)
        if not admin:
            raise LookupError("Admin not found")
        self.repo.delete(admin)
