from __future__ import annotations

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.security import hash_password
from src.models.admin import Admin, AdminRole, AdminStatus

DATABASE_URL = os.environ["DATABASE_URL"]

OWNER_EMAIL = os.environ.get("E2E_ADMIN_EMAIL", "e2e-admin@example.com")
OWNER_PASSWORD = os.environ.get("E2E_ADMIN_PASSWORD", "Passw0rd123!")

SECOND_EMAIL = os.environ.get("E2E_SECOND_ADMIN_EMAIL", "e2e-viewer@example.com")
SECOND_PASSWORD = os.environ.get("E2E_SECOND_ADMIN_PASSWORD", "Passw0rd123!")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def ensure_admin(db, *, email, password, role):
    existing = db.query(Admin).filter(Admin.email == email).first()
    if existing:
        return existing

    admin = Admin(
        name=email.split("@")[0],
        email=email,
        password=hash_password(password),
        role=role,
        is_active=True,
        status=AdminStatus.active,
    )
    db.add(admin)
    db.commit()
    return admin

def main():
    db = SessionLocal()

    ensure_admin(
        db,
        email=OWNER_EMAIL,
        password=OWNER_PASSWORD,
        role=AdminRole.owner,
    )

    ensure_admin(
        db,
        email=SECOND_EMAIL,
        password=SECOND_PASSWORD,
        role=AdminRole.viewer,  # 👈 important
    )

    print("E2E admins ensured")

if __name__ == "__main__":
    main()
