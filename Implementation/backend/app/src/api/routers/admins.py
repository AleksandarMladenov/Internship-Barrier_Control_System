# backend/app/src/api/routers/admins.py

from fastapi import APIRouter, Depends, HTTPException, Query, status
from ...schemas.admin import AdminCreate, AdminRead, AdminUpdate
from ...services.admins import AdminService
from ..deps import get_admin_service

# Auth / RBAC
from ...core.security import get_current_admin, require_role
from ...models.admin import AdminRole

router = APIRouter(prefix="/admins", tags=["admins"])


# ──────────────────────────────────────────────────────────────────────────────
# CREATE (Owner only)
# ──────────────────────────────────────────────────────────────────────────────
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
            verified=payload.verified,
            is_accountant=payload.is_accountant,
            role=payload.role,
            is_active=payload.is_active,
        )
    except ValueError as e:
        # e.g., email already in use
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ──────────────────────────────────────────────────────────────────────────────
# READ (Any authenticated admin)
# ──────────────────────────────────────────────────────────────────────────────
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
def list_admins(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    svc: AdminService = Depends(get_admin_service),
):
    return svc.list(skip=skip, limit=limit)


# ──────────────────────────────────────────────────────────────────────────────
# UPDATE (Owner only)
# ──────────────────────────────────────────────────────────────────────────────
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
            verified=payload.verified,
            is_accountant=payload.is_accountant,
            password=payload.password,
            role=payload.role,
            is_active=payload.is_active,
        )
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ──────────────────────────────────────────────────────────────────────────────
# DELETE (Owner only)
# ──────────────────────────────────────────────────────────────────────────────
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
