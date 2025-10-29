from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Request
import stripe

from ..deps import get_payment_service, get_db
from ...core.settings import settings
from ...repositories.payment_sqlalchemy import PaymentRepository
from ...repositories.session_sqlalchemy import ParkingSessionRepository
from ...services.payments import PaymentService
from ...schemas.payment import PaymentCreate, PaymentRead, PaymentUpdateStatus, PaymentStatus
from ...models.subscription import Subscription



# Stripe currency minimums
STRIPE_MIN_AMOUNT = {
    "EUR": 50,
    "USD": 50,
    "GBP": 30,
}
def min_amount_for(currency: str) -> int:
    return STRIPE_MIN_AMOUNT.get(currency.upper(), 50)


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

@router.post("/checkout")
def create_checkout(session_id: int, svc: PaymentService = Depends(get_payment_service)):
    """
    Returns: {"payment_id": ..., "checkout_url": "..."}
    """
    # ---- 1) Stripe key guard ----
    stripe.api_key = settings.STRIPE_SECRET.get_secret_value() if settings.STRIPE_SECRET else ""
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe secret key not configured")

    # ---- 2) Reuse pending payment if it exists ----
    payments = svc.list(session_id=session_id, subscription_id=None, status=None)
    pending = next((p for p in payments if p.status == "pending"), None)

    if pending is None:

        from ...db.database import SessionLocal
        from ...models.session import Session as SessionModel
        from ...models.plan import Plan

        db = SessionLocal()
        try:
            s = db.get(SessionModel, session_id)
            if not s:
                raise HTTPException(status_code=404, detail="Session not found")
            if s.amount_charged is None or s.amount_charged <= 0 or getattr(s, "status", "") != "awaiting_payment":
                raise HTTPException(status_code=400, detail="Session does not require payment")


            currency = "EUR"
            if getattr(s, "plan_id", None):
                plan = db.get(Plan, s.plan_id)
                if plan and plan.currency:
                    currency = plan.currency.upper()

            amount_cents = int(s.amount_charged)

            min_amt = min_amount_for(currency)
            if amount_cents < min_amt:
                amount_cents = min_amt
        finally:
            db.close()

        payload = PaymentCreate(
            session_id=session_id,
            subscription_id=None,
            currency=currency,
            amount_cents=amount_cents,
            method="card",
        )
        payment = svc.create(payload)
    else:
        payment = pending

    # ---- 4) Create Stripe Checkout ----
    try:
        sess = stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": payment.currency.lower(),
                    "product_data": {"name": f"Parking Session #{session_id}"},
                    "unit_amount": payment.amount_cents,
                },
                "quantity": 1,
            }],
            success_url="http://localhost:8000/payments/success?cs={CHECKOUT_SESSION_ID}",
            cancel_url="http://localhost:8000/payments/cancel",
            metadata={
                "payment_id": str(payment.id),
                "session_id": str(session_id),
                "type": "visitor_session",
            },
        )
        return {"payment_id": payment.id, "checkout_url": sess.url}
    except stripe.error.StripeError:
        raise HTTPException(status_code=502, detail="Stripe error creating checkout session")


@router.post("/webhook")
async def stripe_webhook(request: Request, db=Depends(get_db)):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig,
            secret=settings.STRIPE_WEBHOOK_SECRET.get_secret_value() if settings.STRIPE_WEBHOOK_SECRET else "",
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="invalid_signature")
    except Exception:
        raise HTTPException(status_code=400, detail="invalid_payload")

    payments = PaymentRepository(db)
    sessions = ParkingSessionRepository(db)

    # 1) Subscription checkout completed
    if event["type"] == "checkout.session.completed":
        data = event["data"]["object"]
        mode = data.get("mode")

        # Subscription checkout
        if mode == "subscription":
            stripe_sub_id = data.get("subscription")
            metadata = data.get("metadata") or {}
            sub_id = metadata.get("subscription_id")

            if sub_id and stripe_sub_id:
                sub = db.get(Subscription, int(sub_id))
                if sub:
                    sub.stripe_subscription_id = stripe_sub_id
                    # still pending payment until first invoice succeeds
                    db.commit();
                    db.refresh(sub)
            return {"ok": True}

        #  Visitor checkout
        pid = int(data.get("metadata", {}).get("payment_id", "0") or "0")
        if pid:
            p = payments.get(pid)
            if p:
                payments.set_status(p, "succeeded")
                if p.session_id:
                    s = sessions.get(p.session_id)
                    if s:
                        s.status = "closed" if s.ended_at else "paid"
                        sessions.db.commit()
        return {"ok": True}

    # 2) First charge & renewals for subscriptions
    if event["type"] == "invoice.payment_succeeded":
        invoice = event["data"]["object"]
        stripe_sub_id = invoice.get("subscription")

        if stripe_sub_id:
            sub = db.query(Subscription).filter(
                Subscription.stripe_subscription_id == stripe_sub_id
            ).first()
            if sub and sub.status != "active":
                sub.status = "active"
                db.commit();
                db.refresh(sub)

        return {"ok": True}

    # 3) Subscription canceled
    if event["type"] in {
        "customer.subscription.updated",
        "customer.subscription.deleted",
    }:
        stripe_obj = event["data"]["object"]
        stripe_sub_id = stripe_obj.get("id")
        status = stripe_obj.get("status")

        sub = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == stripe_sub_id
        ).first()

        if sub:
            if status in {"active", "trialing"}:
                sub.status = "active"
            elif status in {"past_due", "unpaid"}:
                sub.status = "paused"
            elif status == "canceled":
                sub.status = "canceled"
            db.commit();
            db.refresh(sub)

        return {"ok": True}

    # Fallback
    return {"ok": True}
