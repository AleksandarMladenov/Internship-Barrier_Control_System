from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone, timedelta
import stripe

from ..deps import get_db, get_subscription_service
from ...services.subscriptions import SubscriptionService
from ...schemas.subscription import (
    SubscriptionCreate, SubscriptionRead, SubscriptionStatusUpdate, SubscriptionActivateOnPayment
)
from ...core.settings import settings
from ...core.security import create_plate_claim_token, decode_plate_claim_token
from ...services.emailer import send_verification_email
from ...models.driver import Driver
from ...models.vehicle import Vehicle
from ...models.plan import Plan, PlanType, BillingPeriod
from ...models.subscription import Subscription
from ...repositories.driver_sqlalchemy import DriverRepository
from ...repositories.vehicle_sqlalchemy import VehicleRepository

# ---------- Stripe Helpers ----------
def _stripe_key() -> str:
    return settings.STRIPE_SECRET.get_secret_value() if hasattr(settings.STRIPE_SECRET, "get_secret_value") else (settings.STRIPE_SECRET or "")

def _ensure_stripe():
    stripe.api_key = _stripe_key()
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe secret key not configured")

def _compute_valid_to(start: datetime, plan: Plan) -> datetime:

    if plan.billing_period == BillingPeriod.year:
        return start + timedelta(days=365)
    return start + timedelta(days=30)


# ---------- Driver + Vehicle Logic ----------
def _get_or_create_driver(db, *, name: str, email: str) -> Driver:
    drepo = DriverRepository(db)
    d = drepo.get_by_email(email)
    if d:
        if not d.name and name:
            d.name = name
            db.commit(); db.refresh(d)
        return d
    return drepo.create(name=name, email=email)

def _visitor_driver(db) -> Driver | None:
    return DriverRepository(db).get_by_email("visitor@system.local")

def _create_or_reassign_vehicle(db, *, driver: Driver, region_code: str, plate_text: str) -> Vehicle:
    vrepo = VehicleRepository(db)
    v = vrepo.get_by_plate(region_code=region_code, plate_text=plate_text)
    if not v:
        return vrepo.create(driver_id=driver.id, region_code=region_code, plate_text=plate_text)

    if v.driver_id == driver.id:
        return v

    visitor = _visitor_driver(db)
    if visitor and v.driver_id == visitor.id:
        v.driver_id = driver.id
        db.commit(); db.refresh(v)
        return v

    raise HTTPException(status_code=409, detail="Plate already associated with another driver")


def _ensure_customer_for_driver(db, driver: Driver) -> str:
    _ensure_stripe()
    if getattr(driver, "stripe_customer_id", None):
        return driver.stripe_customer_id
    cust = stripe.Customer.create(
        name=driver.name or None,
        email=driver.email or None,
        metadata={"driver_id": driver.id},
    )
    driver.stripe_customer_id = cust.id
    db.commit(); db.refresh(driver)
    return cust.id


def _create_subscription_checkout(db, sub: Subscription) -> str:
    _ensure_stripe()
    plan = db.get(Plan, sub.plan_id)
    if not plan or plan.type != PlanType.subscription or not getattr(plan, "stripe_price_id", None):
        raise HTTPException(status_code=400, detail="Plan not configured for Stripe subscriptions")

    vehicle = db.get(Vehicle, sub.vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=400, detail="Subscription vehicle missing")
    driver = db.get(Driver, vehicle.driver_id)
    if not driver:
        raise HTTPException(status_code=400, detail="Vehicle has no driver")

    customer_id = _ensure_customer_for_driver(db, driver)

    try:
        cs = stripe.checkout.Session.create(
            mode="subscription",
            customer=customer_id,
            line_items=[{"price": plan.stripe_price_id, "quantity": 1}],
            allow_promotion_codes=True,
            success_url=f"{settings.PUBLIC_BASE_URL}/subscriptions/success?subscription_id={sub.id}&cs={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.PUBLIC_BASE_URL}/subscriptions/cancel?subscription_id={sub.id}",
            metadata={
                "subscription_id": str(sub.id),
                "plan_id": str(plan.id),
                "vehicle_id": str(sub.vehicle_id),
            },
            subscription_data={
                "metadata": {
                    "subscription_id": str(sub.id),
                    "plan_id": str(plan.id),
                }
            },
        )
        return cs.url
    except stripe.error.StripeError as e:
        message = getattr(e, "user_message", None) or str(e)
        raise HTTPException(status_code=502, detail=f"Stripe error: {message}")


# ========== Router ==========
router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


class ClaimStartPayload(BaseModel):
    name: str
    email: EmailStr
    region_code: str
    plate_text: str
    plan_id: int

@router.post("/claim", status_code=202)
def start_subscription_claim(payload: ClaimStartPayload, db=Depends(get_db)):
    plan = db.get(Plan, payload.plan_id)
    if not plan or plan.type != PlanType.subscription:
        raise HTTPException(status_code=400, detail="Plan must be a subscription plan")

    driver = _get_or_create_driver(db, name=payload.name, email=str(payload.email))

    token = create_plate_claim_token(
        driver_id=driver.id,
        region_code=payload.region_code,
        plate_text=payload.plate_text,
        plan_id=plan.id,
        expires_delta=timedelta(hours=24),
    )

    verify_url = f"{settings.PUBLIC_BASE_URL}/api/subscriptions/verify?token={token}"
    send_verification_email(to=driver.email, verify_url=verify_url)

    return {"ok": True, "message": "Verification email sent"}


@router.get("/verify")
def verify_subscription_claim(
    token: str,
    db=Depends(get_db),
    svc: SubscriptionService = Depends(get_subscription_service),
):
    data = decode_plate_claim_token(token)

    driver = db.get(Driver, data["driver_id"])
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    v = _create_or_reassign_vehicle(
        db,
        driver=driver,
        region_code=data["region_code"],
        plate_text=data["plate_text"],
    )

    now = datetime.now(timezone.utc)
    plan = db.get(Plan, data["plan_id"])

    valid_from = now
    valid_to = _compute_valid_to(valid_from, plan)

    sub = svc.create(
        vehicle_id=v.id,
        plan_id=plan.id,
        valid_from=valid_from,
        valid_to=valid_to,
        auto_renew=True,
    )

    checkout_url = _create_subscription_checkout(db, sub)
    return RedirectResponse(url=checkout_url, status_code=302)


@router.post("", response_model=SubscriptionRead, status_code=201)
def create_subscription(payload: SubscriptionCreate, svc: SubscriptionService = Depends(get_subscription_service)):
    return svc.create(
        vehicle_id=payload.vehicle_id,
        plan_id=payload.plan_id,
        valid_from=payload.valid_from,
        valid_to=payload.valid_to,
        auto_renew=payload.auto_renew,
    )

@router.get("", response_model=list[SubscriptionRead])
def list_subscriptions(
    vehicle_id: int = Query(...),
    svc: SubscriptionService = Depends(get_subscription_service),
):
    return svc.list_for_vehicle(vehicle_id)

@router.get("/{subscription_id}", response_model=SubscriptionRead)
def get_subscription(subscription_id: int, svc: SubscriptionService = Depends(get_subscription_service)):
    return svc.get(subscription_id)

@router.patch("/{subscription_id}/status", response_model=SubscriptionRead)
def update_subscription_status(subscription_id: int, payload: SubscriptionStatusUpdate, svc: SubscriptionService = Depends(get_subscription_service)):
    return svc.set_status(subscription_id, status=payload.status, auto_renew=payload.auto_renew)

@router.delete("/{subscription_id}", status_code=204)
def delete_subscription(subscription_id: int, svc: SubscriptionService = Depends(get_subscription_service)):
    svc.delete(subscription_id)

@router.post("/{subscription_id}/checkout")
def create_subscription_checkout(subscription_id: int, db=Depends(get_db)):
    sub = db.get(Subscription, subscription_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    if sub.status not in {"pending_payment", "paused"}:
        raise HTTPException(status_code=409, detail="Subscription is not payable")

    url = _create_subscription_checkout(db, sub)
    return {"checkout_url": url}
