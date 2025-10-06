from ..repositories.admin_sqlalchemy import AdminRepository
from ..models.admin import Admin
from typing import Optional
from passlib.hash import bcrypt

class AdminService:
    def __init__(self, repo: AdminRepository):
        self.repo = repo

    # helper
    def _hash(self, raw: str) -> str:
        return bcrypt.hash(raw)

    def create(self, *, name: str, email: str, password: str,
               verified: bool = False, is_accountant: bool = False) -> Admin:
        if self.repo.get_by_email(email):
            raise ValueError("Email already in use")
        return self.repo.create(
            name=name,
            email=email,
            password_hash=self._hash(password),
            verified=verified,
            is_accountant=is_accountant,
        )

    def get(self, admin_id: int) -> Optional[Admin]:
        return self.repo.get(admin_id)

    def list(self, *, skip: int = 0, limit: int = 50) -> list[Admin]:
        return self.repo.list(skip=skip, limit=limit)

    def update(self, admin_id: int, *, name: Optional[str] = None,
               verified: Optional[bool] = None,
               is_accountant: Optional[bool] = None,
               password: Optional[str] = None) -> Admin:
        admin = self.repo.get(admin_id)
        if not admin:
            raise LookupError("Admin not found")
        fields = {
            "name": name,
            "verified": verified,
            "is_accountant": is_accountant,
        }
        if password:
            fields["password_hash"] = self._hash(password)
        return self.repo.update(admin, **fields)

    def delete(self, admin_id: int) -> None:
        admin = self.repo.get(admin_id)
        if not admin:
            raise LookupError("Admin not found")
        self.repo.delete(admin)
