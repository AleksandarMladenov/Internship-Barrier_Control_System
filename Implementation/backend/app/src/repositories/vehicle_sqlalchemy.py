from sqlalchemy.orm import Session
from ..models.vehicle import Vehicle

class VehicleRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, *, driver_id: int, region_code: str, plate_text: str) -> Vehicle:
        v = Vehicle(driver_id=driver_id, region_code=region_code, plate_text=plate_text)
        self.db.add(v)
        self.db.commit()
        self.db.refresh(v)
        return v

    def get_by_id(self, vehicle_id: int) -> Vehicle | None:
        return self.db.get(Vehicle, vehicle_id)

    def get_by_plate(self, region_code: str, plate_text: str) -> Vehicle | None:
        return (
            self.db.query(Vehicle)
            .filter(Vehicle.region_code == region_code, Vehicle.plate_text == plate_text)
            .first()
        )

    def list_by_driver(self, driver_id: int) -> list[Vehicle]:
        return (
            self.db.query(Vehicle)
            .filter(Vehicle.driver_id == driver_id)
            .order_by(Vehicle.id.desc())
            .all()
        )
