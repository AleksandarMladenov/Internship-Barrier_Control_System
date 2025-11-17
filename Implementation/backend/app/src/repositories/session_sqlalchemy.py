from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from ..models.session import Session as SessionModel
from datetime import datetime

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
        return (
            self.db.query(SessionModel)
            .options(
                joinedload(SessionModel.vehicle),
                joinedload(SessionModel.plan),
            )
            .filter(SessionModel.id == session_id)
            .first()
        )

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

    def get_recent_open_for_vehicle_since(self, vehicle_id: int, since_utc: datetime):
            return (
                self.db.query(SessionModel)
                .filter(
                    SessionModel.vehicle_id == vehicle_id,
                    SessionModel.ended_at.is_(None),
                    SessionModel.started_at >= since_utc,
                )
                .order_by(SessionModel.id.desc())
                .first()
    )

    def get_latest_awaiting_payment_for_vehicle(self, vehicle_id: int) -> Optional[SessionModel]:
        return (
            self.db.query(SessionModel)
            .filter(
                SessionModel.vehicle_id == vehicle_id,
                SessionModel.status == "awaiting_payment",
                SessionModel.amount_charged.isnot(None),
                SessionModel.ended_at.isnot(None),  # already priced/ended at exit
            )
            .order_by(SessionModel.id.desc())
            .first()
        )

