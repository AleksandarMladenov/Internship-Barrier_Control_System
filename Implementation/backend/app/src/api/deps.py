from sqlalchemy.orm import Session
from fastapi import Depends

from ..db.database import SessionLocal
from ..repositories.vehicle_sqlalchemy import VehicleRepository
from ..services.vehicles import VehicleService
from ..repositories.driver_sqlalchemy import DriverRepository
from ..services.drivers import DriverService

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_vehicle_service(db: Session = Depends(get_db)) -> VehicleService:
    repo = VehicleRepository(db)
    return VehicleService(repo)

def get_driver_service(db: Session = Depends(get_db)) -> DriverService:
    repo = DriverRepository(db)
    return DriverService(repo)