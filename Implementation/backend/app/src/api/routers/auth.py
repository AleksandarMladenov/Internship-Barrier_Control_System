# src/api/routers/auth.py
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from ...core.security import create_access_token, verify_password, get_current_admin, maybe_upgrade_password
from ...core.settings import settings
from ...db.database import get_db
from ...repositories.admin_sqlalchemy import AdminRepository

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class MeOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    verified: bool
    is_accountant: bool
    role: str
    is_active: bool

@router.post("/login")
def login(payload: LoginIn, response: Response, db: Session = Depends(get_db)) -> dict[str, Any]:
    repo = AdminRepository(db)
    admin = repo.get_by_email(payload.email)
    if not admin or not verify_password(payload.password, admin.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if not admin.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    # transparently upgrade legacy pbkdf2 -> bcrypt
    maybe_upgrade_password(admin, payload.password, db)

    token = create_access_token(
        subject=admin.id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    response.set_cookie(
        key=settings.AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=str(settings.AUTH_COOKIE_SAMESITE).lower(),
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    return {"ok": True}

@router.post("/logout")
def logout(response: Response) -> dict[str, bool]:
    response.delete_cookie(settings.AUTH_COOKIE_NAME, path="/")
    return {"ok": True}

@router.get("/me", response_model=MeOut)
def me(current=Depends(get_current_admin)) -> MeOut:
    return MeOut(
        id=current.id,
        name=current.name,
        email=current.email,
        verified=current.verified,
        is_accountant=current.is_accountant,
        role=str(current.role),
        is_active=bool(current.is_active),
    )
