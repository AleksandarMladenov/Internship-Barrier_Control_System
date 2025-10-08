# backend/app/src/api/routers/scans.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..deps import get_db
from ...schemas.scan import EntryScanRequest, EntryScanResponse,  ExitScanRequest, ExitScanResponse
from ...services.gate import GateService

router = APIRouter(prefix="/scans", tags=["scans"])

@router.post("/entry", response_model=EntryScanResponse, status_code=status.HTTP_201_CREATED)
def entry_scan(payload: EntryScanRequest, db: Session = Depends(get_db)):
    svc = GateService(db)
    try:
        result = svc.handle_entry_scan(
            region_code=payload.region_code,
            plate_text=payload.plate_text,
            gate_id=payload.gate_id,
            source=payload.source,
        )
    except HTTPException as e:
        # AC: clear, helpful, consistent
        if e.status_code == 403:
            raise HTTPException(status_code=403, detail=e.detail)  # "blacklisted" | "not_allowed"
        raise HTTPException(status_code=400, detail="Invalid request")

    return EntryScanResponse(**result)
@router.post("/exit", response_model=ExitScanResponse, status_code=status.HTTP_200_OK)
def exit_scan(payload: ExitScanRequest, db: Session = Depends(get_db)):
    svc = GateService(db)
    result = svc.handle_exit_scan(
        region_code=payload.region_code,
        plate_text=payload.plate_text,
        gate_id=payload.gate_id,
        source=payload.source,
    )
    return ExitScanResponse(**result)
