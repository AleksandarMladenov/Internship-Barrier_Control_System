# src/api/routers/auth.py
from datetime import timedelta, datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from ...core.security import (
    create_access_token,
    verify_password,
    get_current_admin,
    maybe_upgrade_password,
    hash_password,  # <-- use this
)
from ...core.settings import settings
from ...db.database import get_db
from ...repositories.admin_sqlalchemy import AdminRepository
from ...models.admin import AdminStatus
from ...schemas.admin import AcceptInviteIn

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class MeOut(BaseModel):
    id: int
    name: str
    email: EmailStr
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
        role=current.role.value,
        is_active=bool(current.is_active),
    )


@router.post("/accept-invite")
def accept_invite(payload: AcceptInviteIn, response: Response, db: Session = Depends(get_db)):
    repo = AdminRepository(db)
    admin = repo.get_by_invited_token(payload.token)

    if not admin or admin.status != AdminStatus.invited:
        raise HTTPException(status_code=400, detail="Invalid or already used invite")

    if admin.invited_expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invite expired")

    hashed = hash_password(payload.password)  # <-- correct call
    repo.activate_from_invite(admin, hashed, name=payload.name)

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
