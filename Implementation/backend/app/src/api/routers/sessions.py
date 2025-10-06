from fastapi import APIRouter, Depends, Query
from typing import Optional

from ..deps import get_session_service
from ...schemas.session import SessionCreate, SessionRead, SessionEnd
from ...services.sessions import ParkingSessionService

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.post("", response_model=SessionRead, status_code=201)
def start_session(
    payload: SessionCreate,
    svc: ParkingSessionService = Depends(get_session_service),
):
    return svc.start(vehicle_id=payload.vehicle_id, started_at=payload.started_at)

@router.get("/{session_id}", response_model=SessionRead)
def get_session(
    session_id: int,
    svc: ParkingSessionService = Depends(get_session_service),
):
    return svc.get(session_id)

@router.get("", response_model=list[SessionRead])
def list_sessions(
    vehicle_id: int = Query(..., description="Filter by vehicle"),
    svc: ParkingSessionService = Depends(get_session_service),
):
    return svc.list_for_vehicle(vehicle_id)

@router.post("/{session_id}/end", response_model=SessionRead)
def end_session(
    session_id: int,
    payload: SessionEnd,
    svc: ParkingSessionService = Depends(get_session_service),
):
    return svc.end(session_id, ended_at=payload.ended_at)

@router.delete("/{session_id}", status_code=204)
def delete_session(
    session_id: int,
    svc: ParkingSessionService = Depends(get_session_service),
):
    svc.delete(session_id)
