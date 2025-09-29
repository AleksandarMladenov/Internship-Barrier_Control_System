from fastapi import APIRouter, Depends, HTTPException, Query
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

@router.get("", response_model=list[VehicleRead])
def list_vehicles(
    driver_id: int = Query(..., description="Filter vehicles by driver"),
    svc: VehicleService = Depends(get_vehicle_service),
):
    return svc.list_for_driver(driver_id)
