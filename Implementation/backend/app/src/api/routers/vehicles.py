from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ...core.security import get_current_admin
from ...db.database import get_db
from ...models import Vehicle
from ...services.vehicles import VehicleService
from ...schemas.vehicle import VehicleCreate, VehicleRead
from ..deps import get_vehicle_service

router = APIRouter(prefix="/vehicles", tags=["vehicles"])

@router.post("", response_model=VehicleRead)
def register_vehicle(
    payload: VehicleCreate,
    svc: VehicleService = Depends(get_vehicle_service),
):
    try:
        v = svc.register(driver_id=payload.driver_id,
                         region_code=payload.region_code,
                         plate_text=payload.plate_text)
        return v
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{vehicle_id}", response_model=VehicleRead)
def get_vehicle(
    vehicle_id: int,
    svc: VehicleService = Depends(get_vehicle_service),
):
    v = svc.get(vehicle_id)
    if not v:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return v

@router.get("")   # NOTE: no response_model so we can return {items,total}
def list_vehicles(
    q: str = Query("", min_length=0),
    # previously required — now OPTIONAL
    driver_id: int | None = Query(None, description="Filter by driver if provided"),
    # UI filters
    is_blacklisted: bool | None = Query(None),
    status: str | None = Query(None, description="Only used if Vehicle has a status column"),
    # pagination
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),

    db: Session = Depends(get_db),
    _admin = Depends(get_current_admin),  # protect with admin auth
):
    query = db.query(Vehicle)

    if driver_id is not None:
        query = query.filter(Vehicle.driver_id == driver_id)

    if q:
        like = f"%{q.lower()}%"
        query = query.filter(
            (func.lower(Vehicle.region_code).like(like)) |
            (func.lower(Vehicle.plate_text).like(like))
        )

    if is_blacklisted is not None:
        query = query.filter(Vehicle.is_blacklisted == is_blacklisted)

    if status:
        try:
            getattr(Vehicle, "status")
            query = query.filter(func.lower(Vehicle.status).like(f"%{status.lower()}%"))
        except AttributeError:
            pass

    total = query.count()
    items = (
        query.order_by(Vehicle.id.desc())
             .offset((page - 1) * page_size)
             .limit(page_size)
             .all()
    )

    return {
        "items": items,
        "total": total,
    }
