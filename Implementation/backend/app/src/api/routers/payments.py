from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Request
import stripe

from ..deps import get_payment_service, get_db
from ...core.settings import settings
from ...models import Vehicle
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

#change
@router.get("/id/{payment_id}", response_model=PaymentRead)
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

#change
@router.post("/checkout")
def create_checkout(
    session_id: int,
    svc: PaymentService = Depends(get_payment_service),
    db = Depends(get_db),
):
    """
    Returns: {"payment_id": <int>, "checkout_url": <str>}
    Preconditions:
      - Session exists
      - Session.status == "awaiting_payment"
      - Session.amount_charged > 0 (will be clamped to Stripe minimums per currency)
    """
    # ---- 1) Stripe key guard ----
    stripe.api_key = settings.STRIPE_SECRET.get_secret_value() if settings.STRIPE_SECRET else ""
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe secret key not configured")

    # ---- 2) Reuse pending payment if it exists ----
    payments = svc.list(session_id=session_id, subscription_id=None, status=None)
    pending = next((p for p in payments if p.status == "pending"), None)

    if pending is None:
        # Use the injected DB session
        from ...models.session import Session as SessionModel
        from ...models.plan import Plan

        s = db.get(SessionModel, session_id)
        if not s:
            raise HTTPException(status_code=404, detail="Session not found")

        if s.amount_charged is None or s.amount_charged <= 0 or (getattr(s, "status", "") != "awaiting_payment"):
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

    # ---- 3) Create Stripe Checkout ----
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
            #  add this so PI carries the references
            payment_intent_data={
                "metadata": {
                    "payment_id": str(payment.id),
                    "session_id": str(session_id),
                    "type": "visitor_session",
                }
            },
            # keep metadata on the CS too
            metadata={
                "payment_id": str(payment.id),
                "session_id": str(session_id),
                "type": "visitor_session",
            },
            success_url="http://localhost:5173/receipt?cs={CHECKOUT_SESSION_ID}",
            cancel_url="http://localhost:5173/visitor?cancelled=true",
        )

        # persist BOTH ids (uses your PaymentRepository.attach_stripe_ids)
        repo = PaymentRepository(db)
        repo.attach_stripe_ids(
            repo.get(payment.id),
            checkout_id=sess.get("id"),
            payment_intent_id=sess.get("payment_intent"),
        )

        return {"payment_id": payment.id, "checkout_url": sess.url}

    except stripe.error.StripeError as e:
        msg = getattr(e, "user_message", None) or str(e)
        raise HTTPException(status_code=502, detail=f"stripe_error: {msg}")


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

        # 2) PaymentIntent succeeded (fallback)
    if event["type"] == "payment_intent.succeeded":
        pi = event["data"]["object"]
        pi_id = pi.get("id")

        p = payments.get_by_payment_intent(pi_id) if pi_id else None
        if not p:
            meta = (pi.get("metadata") or {})
            pid = int(meta.get("payment_id") or 0)
            if pid:
                p = payments.get(pid)

        if p:
            if p.status != "succeeded":
                payments.set_status(p, "succeeded")
            if p.session_id:
                s = sessions.get(p.session_id)
                if s:
                    s.status = "closed" if s.ended_at else "paid"
                    sessions.db.commit()
        return {"ok": True}

    # 3) First charge & renewals for subscriptions
    if event["type"] == "invoice.payment_succeeded":
        invoice = event["data"]["object"]
        stripe_sub_id = invoice.get("subscription")

        if stripe_sub_id:
            sub = db.query(Subscription).filter(
                Subscription.stripe_subscription_id == stripe_sub_id
            ).first()
            if sub and sub.status != "active":
                sub.status = "active"
                #  ensure vehicle is whitelisted when payment lands
                veh = db.get(Vehicle, sub.vehicle_id)
                if veh and veh.is_blacklisted:
                    veh.is_blacklisted = False
                db.commit()
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

@router.get("/resolve")
def resolve_checkout_session(cs: str, db=Depends(get_db)):
    payment = PaymentRepository(db).get_by_checkout_session_id(cs)
    if not payment or not payment.session_id:
        raise HTTPException(status_code=404, detail="not_found")
    return {"session_id": payment.session_id}

@router.post("/confirm")
def confirm_checkout(cs: str, db = Depends(get_db)):
    stripe.api_key = settings.STRIPE_SECRET.get_secret_value() if settings.STRIPE_SECRET else ""
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe secret key not configured")

    try:
        cs_obj = stripe.checkout.Session.retrieve(cs)
    except stripe.error.StripeError as e:
        msg = getattr(e, "user_message", None) or str(e)
        raise HTTPException(status_code=502, detail=f"stripe_error: {msg}")

    repo = PaymentRepository(db)
    sess_repo = ParkingSessionRepository(db)

    p = repo.get_by_checkout_session_id(cs_obj.get("id"))
    if not p and cs_obj.get("payment_intent"):
        p = repo.get_by_payment_intent(cs_obj.get("payment_intent"))

    if not p:
        raise HTTPException(status_code=404, detail="payment_not_found")

    if cs_obj.get("payment_status") == "paid" and p.status != "succeeded":
        repo.set_status(p, "succeeded")
        if p.session_id:
            s = sess_repo.get(p.session_id)
            if s:
                s.status = "closed" if s.ended_at else "paid"
                sess_repo.db.commit()

    return {"ok": True, "session_id": p.session_id}


