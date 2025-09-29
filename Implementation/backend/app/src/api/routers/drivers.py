from fastapi import APIRouter, Depends, HTTPException
from ...schemas.driver import DriverCreate, DriverRead
from ...services.drivers import DriverService
from ..deps import get_driver_service

router = APIRouter(prefix="/drivers", tags=["drivers"])

@router.post("", response_model=DriverRead)
def register_driver(payload: DriverCreate, svc: DriverService = Depends(get_driver_service)):
    try:
        return svc.register(name=payload.name, email=payload.email)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{driver_id}", response_model=DriverRead)
def get_driver(driver_id: int, svc: DriverService = Depends(get_driver_service)):
    d = svc.get(driver_id)
    if not d:
        raise HTTPException(status_code=404, detail="Driver not found")
    return d

@router.get("", response_model=list[DriverRead])
def list_drivers(svc: DriverService = Depends(get_driver_service)):
    return svc.list()
