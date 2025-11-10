from sqlalchemy import func
from sqlalchemy.orm import Session
from ..models.vehicle import Vehicle

class VehicleRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, *, driver_id: int, region_code: str, plate_text: str) -> Vehicle:
        v = Vehicle(
            driver_id=driver_id,
            region_code=region_code.upper().strip(),
            plate_text=plate_text.upper().strip(),
        )
        self.db.add(v)
        self.db.commit()
        self.db.refresh(v)
        return v

    def get_by_id(self, vehicle_id: int) -> Vehicle | None:
        return self.db.get(Vehicle, vehicle_id)

    def get_by_plate(self, region_code: str, plate_text: str) -> Vehicle | None:
        return (
            self.db.query(Vehicle)
            .filter(
                func.upper(Vehicle.region_code) == region_code.upper(),
                func.upper(Vehicle.plate_text) == plate_text.upper(),
            )
            .first()
        )

    def list_by_driver(self, driver_id: int) -> list[Vehicle]:
        return (
            self.db.query(Vehicle)
            .filter(Vehicle.driver_id == driver_id)
            .order_by(Vehicle.id.desc())
            .all()
        )
    def set_blacklist(self, vehicle_id: int, blacklisted: bool) -> Vehicle | None:
        v = self.db.get(Vehicle, vehicle_id)
        if not v:
            return None
        v.is_blacklisted = blacklisted
        self.db.commit()
        self.db.refresh(v)
        return v

    def delete_if_blacklisted(self, vehicle_id: int) -> bool:
        """Delete the vehicle only if it is blacklisted. Return True if deleted."""
        v = self.get_by_id(vehicle_id)
        if not v:
            return False
        if not v.is_blacklisted:
            return False

        self.db.delete(v)
        self.db.commit()
        return True