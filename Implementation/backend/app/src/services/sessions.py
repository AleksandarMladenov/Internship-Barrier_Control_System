from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session as SASession

from ..models.vehicle import Vehicle
from ..models.session import Session as SessionModel
from ..repositories.session_sqlalchemy import ParkingSessionRepository

class ParkingSessionService:
    """
    Business rules:
    - A vehicle may have at most one *active* session (ended_at is NULL).
    - When ending a session, ended_at must be >= started_at.
    - Optional: prevent deleting sessions that have succeeded payments (commented stub).
    """
    def __init__(self, repo: ParkingSessionRepository):
        self.repo = repo
        self.db: SASession = repo.db

    def _ensure_vehicle(self, vehicle_id: int) -> None:
        if self.db.get(Vehicle, vehicle_id) is None:
            raise HTTPException(status_code=404, detail="Vehicle not found")

    def start(self, *, vehicle_id: int, started_at: datetime | None = None) -> SessionModel:
        self._ensure_vehicle(vehicle_id)

        # Enforce single active session per vehicle
        active = self.repo.get_active_for_vehicle(vehicle_id)
        if active is not None:
            raise HTTPException(status_code=409, detail="Vehicle already has an active session")

        # If client didn't provide started_at, let DB default (server_default=now()).
        # If provided, use it.
        if started_at is None:
            # creating without started_at allows DB to fill server_default
            return self.repo.create(vehicle_id=vehicle_id)
        else:
            return self.repo.create(vehicle_id=vehicle_id, started_at=started_at)

    def get(self, session_id: int) -> SessionModel:
        s = self.repo.get(session_id)
        if not s:
            raise HTTPException(status_code=404, detail="Session not found")
        return s

    def list_for_vehicle(self, vehicle_id: int) -> list[SessionModel]:
        self._ensure_vehicle(vehicle_id)
        return self.repo.list_by_vehicle(vehicle_id)

    def end(self, session_id: int, *, ended_at: datetime | None) -> SessionModel:
        s = self.get(session_id)
        if s.ended_at is not None:
            raise HTTPException(status_code=400, detail="Session already ended")

        # Default to now (UTC) if not provided
        end_ts = ended_at or datetime.now(timezone.utc)

        if s.started_at and end_ts < s.started_at:
            raise HTTPException(status_code=400, detail="ended_at must be >= started_at")

        return self.repo.end_session(s, ended_at=end_ts)

    def delete(self, session_id: int) -> None:
        s = self.get(session_id)

        # Optional safety: don't allow delete if it has succeeded payments
        # from ..models.payment import Payment
        # exists = (
        #     self.db.query(Payment)
        #     .filter(Payment.session_id == s.id, Payment.status == "succeeded")
        # ).first()
        # if exists:
        #     raise HTTPException(status_code=409, detail="Session has settled payments and cannot be deleted")

        self.repo.delete(s)
