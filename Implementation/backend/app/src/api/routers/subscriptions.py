from fastapi import APIRouter, Depends, Query
from ..deps import get_subscription_service
from ...services.subscriptions import SubscriptionService
from ...schemas.subscription import (
    SubscriptionCreate, SubscriptionRead, SubscriptionStatusUpdate, SubscriptionActivateOnPayment
)

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

@router.post("", response_model=SubscriptionRead, status_code=201)
def create_subscription(
    payload: SubscriptionCreate,
    svc: SubscriptionService = Depends(get_subscription_service),
):
    return svc.create(
        vehicle_id=payload.vehicle_id,
        plan_id=payload.plan_id,
        valid_from=payload.valid_from,
        valid_to=payload.valid_to,
        auto_renew=payload.auto_renew,
    )

@router.get("/{subscription_id}", response_model=SubscriptionRead)
def get_subscription(
    subscription_id: int,
    svc: SubscriptionService = Depends(get_subscription_service),
):
    return svc.get(subscription_id)

@router.get("", response_model=list[SubscriptionRead])
def list_subscriptions(
    vehicle_id: int = Query(..., description="Filter by vehicle"),
    svc: SubscriptionService = Depends(get_subscription_service),
):
    return svc.list_for_vehicle(vehicle_id)

@router.patch("/{subscription_id}/status", response_model=SubscriptionRead)
def update_subscription_status(
    subscription_id: int,
    payload: SubscriptionStatusUpdate,
    svc: SubscriptionService = Depends(get_subscription_service),
):
    return svc.set_status(subscription_id, status=payload.status, auto_renew=payload.auto_renew)

@router.post("/{subscription_id}/activate-on-payment", response_model=SubscriptionRead)
def activate_subscription_after_payment(
    subscription_id: int,
    _: SubscriptionActivateOnPayment,
    svc: SubscriptionService = Depends(get_subscription_service),
):
    return svc.activate_on_payment(subscription_id)

@router.delete("/{subscription_id}", status_code=204)
def delete_subscription(
    subscription_id: int,
    svc: SubscriptionService = Depends(get_subscription_service),
):
    svc.delete(subscription_id)
