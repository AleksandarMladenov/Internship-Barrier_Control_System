from typing import Optional
from fastapi import APIRouter, Depends, Query

from ..deps import get_payment_service
from ...services.payments import PaymentService
from ...schemas.payment import PaymentCreate, PaymentRead, PaymentUpdateStatus, PaymentStatus

router = APIRouter(prefix="/payments", tags=["payments"])

@router.post("", response_model=PaymentRead, status_code=201)
def create_payment(
    payload: PaymentCreate,
    svc: PaymentService = Depends(get_payment_service),
):
    return svc.create(payload)

@router.get("/{payment_id}", response_model=PaymentRead)
def get_payment(
    payment_id: int,
    svc: PaymentService = Depends(get_payment_service),
):
    return svc.get(payment_id)

@router.get("", response_model=list[PaymentRead])
def list_payments(
    session_id: Optional[int] = Query(default=None),
    subscription_id: Optional[int] = Query(default=None),
    status: Optional[PaymentStatus] = Query(default=None),
    svc: PaymentService = Depends(get_payment_service),
):
    return svc.list(session_id=session_id, subscription_id=subscription_id, status=status)

@router.post("/{payment_id}/status", response_model=PaymentRead)
def set_payment_status(
    payment_id: int,
    payload: PaymentUpdateStatus,
    svc: PaymentService = Depends(get_payment_service),
):
    return svc.set_status(payment_id, payload.status)

@router.delete("/{payment_id}", status_code=204)
def delete_payment(
    payment_id: int,
    svc: PaymentService = Depends(get_payment_service),
):
    svc.delete(payment_id)
