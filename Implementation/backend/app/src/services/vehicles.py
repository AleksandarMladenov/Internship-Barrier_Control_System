from ..models.vehicle import Vehicle
from ..repositories.vehicle_sqlalchemy import VehicleRepository

class VehicleService:
    def __init__(self, repo: VehicleRepository):
        self.repo = repo

    def register(self, *, driver_id: int, region_code: str, plate_text: str) -> Vehicle:
        existing = self.repo.get_by_plate(region_code, plate_text)
        if existing:
            raise ValueError("Vehicle already registered")
        return self.repo.create(driver_id=driver_id, region_code=region_code, plate_text=plate_text)

    def get(self, vehicle_id: int) -> Vehicle | None:
        return self.repo.get_by_id(vehicle_id)

    def list_for_driver(self, driver_id: int) -> list[Vehicle]:
        return self.repo.list_by_driver(driver_id)
