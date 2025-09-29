from sqlalchemy.orm import Session
from ..models.driver import Driver

class DriverRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, *, name: str, email: str) -> Driver:
        d = Driver(name=name, email=email)
        self.db.add(d)
        self.db.commit()
        self.db.refresh(d)
        return d

    def get_by_id(self, driver_id: int) -> Driver | None:
        return self.db.get(Driver, driver_id)

    def get_by_email(self, email: str) -> Driver | None:
        return self.db.query(Driver).filter(Driver.email == email).first()

    def list(self) -> list[Driver]:
        return self.db.query(Driver).order_by(Driver.id.desc()).all()
