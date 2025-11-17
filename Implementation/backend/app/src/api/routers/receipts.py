# app/src/api/routers/receipts.py
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from ..deps import get_db
from ...repositories.session_sqlalchemy import ParkingSessionRepository
from ...services.emailer import send_receipt_email

router = APIRouter(prefix="/receipts", tags=["receipts"])


class ReceiptEmailPayload(BaseModel):
    session_id: int
    email: EmailStr


@router.post("/email", status_code=204)
def send_receipt_to_email(
    payload: ReceiptEmailPayload,
    db=Depends(get_db),
):
    """
    Send a parking receipt email for a finished session.
    Request body: { "session_id": 42, "email": "user@example.com" }
    """

    sessions = ParkingSessionRepository(db)
    s = sessions.get(payload.session_id)
    if not s:
        raise HTTPException(status_code=404, detail="session_not_found")

    # build plate + currency info
    region = getattr(getattr(s, "vehicle", None), "region_code", None) or ""
    plate = getattr(getattr(s, "vehicle", None), "plate_text", None) or ""
    plate_full = f"{region}{plate}"

    currency: str = "EUR"
    if getattr(s, "plan", None) and getattr(s.plan, "currency", None):
        currency = s.plan.currency

    ok = send_receipt_email(
        to=payload.email,
        session_id=s.id,
        plate_full=plate_full,
        started_at=s.started_at,
        ended_at=s.ended_at,
        amount_cents=s.amount_charged,
        currency=currency,
    )

    if not ok:

        raise HTTPException(status_code=503, detail="email_disabled")

    return
