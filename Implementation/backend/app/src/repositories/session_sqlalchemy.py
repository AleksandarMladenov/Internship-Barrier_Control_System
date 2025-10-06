from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models.session import Session as SessionModel

class ParkingSessionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs) -> SessionModel:
        s = SessionModel(**kwargs)
        self.db.add(s)
        self.db.commit()
        self.db.refresh(s)
        return s

    def get(self, session_id: int) -> Optional[SessionModel]:
        return self.db.get(SessionModel, session_id)

    def list_by_vehicle(self, vehicle_id: int) -> List[SessionModel]:
        return (
            self.db.query(SessionModel)
            .filter(SessionModel.vehicle_id == vehicle_id)
            .order_by(SessionModel.id.desc())
            .all()
        )

    def get_active_for_vehicle(self, vehicle_id: int) -> Optional[SessionModel]:
        return (
            self.db.query(SessionModel)
            .filter(SessionModel.vehicle_id == vehicle_id, SessionModel.ended_at.is_(None))
            .order_by(SessionModel.id.desc())
            .first()
        )

    def end_session(self, s: SessionModel, *, ended_at) -> SessionModel:
        s.ended_at = ended_at
        self.db.commit()
        self.db.refresh(s)
        return s

    def delete(self, s: SessionModel) -> None:
        self.db.delete(s)
        self.db.commit()
