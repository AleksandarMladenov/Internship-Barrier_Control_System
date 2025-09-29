from ..models.driver import Driver
from ..repositories.driver_sqlalchemy import DriverRepository

class DriverService:
    def __init__(self, repo: DriverRepository):
        self.repo = repo

    def register(self, *, name: str, email: str) -> Driver:
        if self.repo.get_by_email(email):
            raise ValueError("Driver with this email already exists")
        return self.repo.create(name=name, email=email)

    def get(self, driver_id: int) -> Driver | None:
        return self.repo.get_by_id(driver_id)

    def list(self) -> list[Driver]:
        return self.repo.list()
