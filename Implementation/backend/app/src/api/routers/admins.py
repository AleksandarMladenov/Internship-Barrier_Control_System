from fastapi import APIRouter, Depends, HTTPException, Query
from ...schemas.admin import AdminCreate, AdminRead, AdminUpdate
from ...services.admins import AdminService
from ..deps import get_admin_service

router = APIRouter(prefix="/admins", tags=["admins"])

@router.post("", response_model=AdminRead, status_code=201)
def create_admin(payload: AdminCreate, svc: AdminService = Depends(get_admin_service)):
    try:
        return svc.create(
            name=payload.name,
            email=payload.email,
            password=payload.password,
            verified=payload.verified,
            is_accountant=payload.is_accountant,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{admin_id}", response_model=AdminRead)
def get_admin(admin_id: int, svc: AdminService = Depends(get_admin_service)):
    obj = svc.get(admin_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Admin not found")
    return obj

@router.get("", response_model=list[AdminRead])
def list_admins(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    svc: AdminService = Depends(get_admin_service),
):
    return svc.list(skip=skip, limit=limit)

@router.patch("/{admin_id}", response_model=AdminRead)
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
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{admin_id}", status_code=204)
def delete_admin(admin_id: int, svc: AdminService = Depends(get_admin_service)):
    try:
        svc.delete(admin_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
