from fastapi import APIRouter, Depends, HTTPException, Query, status, Request, Body
from sqlalchemy.orm import Session

# Repos & DB
from ...db.database import get_db
from ...repositories.admin_sqlalchemy import AdminRepository

# Models / Security / Settings
from ...models.admin import AdminRole, AdminStatus, Admin as AdminModel
from ...core.security import get_current_admin, require_role
from ...core.settings import settings

# Schemas
from ...schemas.admin import (
    AdminCreate,
    AdminRead,
    AdminUpdate,
    AdminInviteIn,
    AdminInviteOut,
)
from ...services.access_list import AccessListService

# Services (you already had these wired)
from ...services.admins import AdminService
from ..deps import get_admin_service

# Email
from ...services.emailer import send_invite_email

router = APIRouter(prefix="/admins", tags=["admins"])

# ──────────────────────────────────────────────────────────────────────────────
# INVITE FLOW (Owner/Admin)
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/invite", response_model=AdminInviteOut, status_code=status.HTTP_201_CREATED)
def invite_admin(
    payload: AdminInviteIn,
    request: Request,
    db: Session = Depends(get_db),
    actor: AdminModel = Depends(get_current_admin),
):
    # permissions: owner can invite anyone; admin cannot invite owner
    if actor.role == AdminRole.admin and payload.role == AdminRole.owner:
        raise HTTPException(status_code=403, detail="Admin cannot invite owner")
    if actor.role not in (AdminRole.owner, AdminRole.admin):
        raise HTTPException(status_code=403, detail="Only owners/admins can invite")

    repo = AdminRepository(db)
    existing = repo.get_by_email(payload.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already exists")

    invited = repo.create_invited(
        email=payload.email,
        role=payload.role,
        invited_by_id=actor.id,
        name=payload.name,
        expires_minutes=settings.INVITE_EXPIRES_MINUTES,
    )

    # build invite link
    base = settings.FRONTEND_BASE_URL.rstrip("/")
    invite_url = f"{base}/accept-invite?token={invited.invited_token}"

    sent = False
    # optional email (do not fail if SMTP misconfigured)
    try:
        send_invite_email(invited.email, invite_url)
    except Exception:
        pass

    return AdminInviteOut(
        id=invited.id,
        email=invited.email,
        role=invited.role,
        status=invited.status,
        invite_url=invite_url,
        email_sent=sent,
    )


@router.post("/{admin_id}/resend-invite", response_model=AdminInviteOut)
def resend_invite(
    admin_id: int,
    db: Session = Depends(get_db),
    actor: AdminModel = Depends(get_current_admin),
):
    repo = AdminRepository(db)
    target = repo.get(admin_id)
    if not target:
        raise HTTPException(status_code=404, detail="Admin not found")
    if target.status != AdminStatus.invited:
        raise HTTPException(status_code=400, detail="Only invited users can be resent an invite")

    # permissions: admin cannot manage owner, cannot manage self
    try:
        repo.assert_can_manage(actor, target)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    # regenerate invite by creating a fresh token/expiry and assigning to current row
    fresh = repo.create_invited(
        email=target.email,
        role=target.role,
        invited_by_id=actor.id,
        name=target.name,
        expires_minutes=settings.INVITE_EXPIRES_MINUTES,
    )
    target.invited_token = fresh.invited_token
    target.invited_expires_at = fresh.invited_expires_at
    db.commit()
    db.refresh(target)

    invite_url = f"{settings.FRONTEND_BASE_URL.rstrip('/')}/accept-invite?token={target.invited_token}"
    try:
        send_invite_email(target.email, invite_url)
    except Exception:
        pass

    return AdminInviteOut(
        id=target.id,
        email=target.email,
        role=target.role,
        status=target.status,
        invite_url=invite_url,
    )


@router.post("/{admin_id}/deactivate", response_model=AdminRead)
def deactivate_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    actor: AdminModel = Depends(get_current_admin),
):
    repo = AdminRepository(db)
    target = repo.get(admin_id)
    if not target:
        raise HTTPException(status_code=404, detail="Admin not found")

    try:
        repo.assert_can_manage(actor, target)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    if target.role == AdminRole.owner and repo.count_owners() <= 1:
        raise HTTPException(status_code=400, detail="Cannot disable the last owner")

    return repo.deactivate(target)


@router.post("/{admin_id}/activate", response_model=AdminRead)
def activate_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    actor: AdminModel = Depends(get_current_admin),
):
    repo = AdminRepository(db)
    target = repo.get(admin_id)
    if not target:
        raise HTTPException(status_code=404, detail="Admin not found")

    try:
        repo.assert_can_manage(actor, target)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    return repo.reactivate(target)



@router.post(
    "",
    response_model=AdminRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(AdminRole.owner))],
)
def create_admin(payload: AdminCreate, svc: AdminService = Depends(get_admin_service)):
    try:
        return svc.create(
            name=payload.name,
            email=payload.email,
            password=payload.password,
            role=payload.role,
            is_active=payload.is_active,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{admin_id}",
    response_model=AdminRead,
    dependencies=[Depends(get_current_admin)],
)
def get_admin(admin_id: int, svc: AdminService = Depends(get_admin_service)):
    obj = svc.get(admin_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")
    return obj


@router.get(
    "",
    response_model=list[AdminRead],
    dependencies=[Depends(get_current_admin)],
)
def list_admins_legacy(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    svc: AdminService = Depends(get_admin_service),
):
    return svc.list(skip=skip, limit=limit)


@router.patch(
    "/{admin_id}",
    response_model=AdminRead,
    dependencies=[Depends(require_role(AdminRole.owner))],
)
def update_admin(
    admin_id: int,
    payload: AdminUpdate,
    svc: AdminService = Depends(get_admin_service),
):
    try:
        return svc.update(
            admin_id,
            name=payload.name,
            password=payload.password,
            role=payload.role,
            is_active=payload.is_active,
            status=payload.status,  # remove if your service doesn't accept it
        )
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/{admin_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role(AdminRole.owner))],
)
def delete_admin(admin_id: int, svc: AdminService = Depends(get_admin_service)):
    try:
        svc.delete(admin_id)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("/access/blacklist/{vehicle_id}")
def admin_blacklist_vehicle(
    vehicle_id: int,
    reason: str | None = Body(None),
    db: Session = Depends(get_db),
    current_admin = Depends(require_role(AdminRole.admin)),
):
    svc = AccessListService(db)
    try:
        v = svc.blacklist(admin_id=current_admin.id, vehicle_id=vehicle_id, reason=reason)
        return {"vehicle_id": v.id, "is_blacklisted": v.is_blacklisted, "status": "ok"}
    except ValueError:
        raise HTTPException(status_code=404, detail="vehicle_not_found")

@router.post("/access/whitelist/{vehicle_id}")
def admin_whitelist_vehicle(
    vehicle_id: int,
    reason: str | None = Body(None),
    resume_suspended: bool = False,
    db: Session = Depends(get_db),
    current_admin = Depends(require_role(AdminRole.admin)),
):
    svc = AccessListService(db)
    try:
        v = svc.whitelist(admin_id=current_admin.id, vehicle_id=vehicle_id, reason=reason, resume_suspended=resume_suspended)
        return {"vehicle_id": v.id, "is_blacklisted": v.is_blacklisted, "status": "ok"}
    except ValueError:
        raise HTTPException(status_code=404, detail="vehicle_not_found")

@router.delete("/access/blacklist/{vehicle_id}")
def admin_delete_blacklisted_vehicle(
    vehicle_id: int,
    reason: str | None = Body(None),
    db: Session = Depends(get_db),
    current_admin = Depends(require_role(AdminRole.admin)),
):
    svc = AccessListService(db)
    try:
        svc.delete_blacklisted(admin_id=current_admin.id, vehicle_id=vehicle_id, reason=reason)
        return {"vehicle_id": vehicle_id, "deleted": True, "status": "ok"}
    except ValueError as e:
        detail = str(e)
        if detail == "vehicle_not_found":
            raise HTTPException(status_code=404, detail=detail)
        if detail == "vehicle_not_blacklisted":
            raise HTTPException(status_code=409, detail=detail)
        raise HTTPException(status_code=400, detail="delete_failed")
