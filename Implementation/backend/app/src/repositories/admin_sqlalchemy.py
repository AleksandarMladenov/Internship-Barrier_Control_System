from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models.admin import Admin

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
