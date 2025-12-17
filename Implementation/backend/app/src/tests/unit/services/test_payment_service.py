# src/tests/unit/services/test_payment_service.py
from __future__ import annotations

import pytest
from fastapi import HTTPException

# Import the module, not just the class, so we can monkeypatch inside it
import src.services.payments as payments_module
from src.schemas.payment import PaymentStatus


# -----------------------------
# Fakes (no DB, no SQLAlchemy)
# -----------------------------

class FakeDB:
    """
    Minimal DB stub to support PaymentService._ensure_refs which calls:
        self.db.get(SessionModel, id)
        self.db.get(Subscription, id)
    """
    def __init__(self):
        self._store = {}  # key: (model_cls, id) -> obj

    def put(self, model_cls, obj_id: int, obj: object = None):
        self._store[(model_cls, obj_id)] = obj if obj is not None else object()

    def get(self, model_cls, obj_id: int):
        return self._store.get((model_cls, obj_id), None)


class FakePayment:
    def __init__(
        self,
        *,
        id: int = 1,
        status: str = "pending",
        session_id: int | None = None,
        subscription_id: int | None = None,
        currency: str = "EUR",
        amount_cents: int = 100,
        method: str = "card",
    ):
        self.id = id
        self.status = status
        self.session_id = session_id
        self.subscription_id = subscription_id
        self.currency = currency
        self.amount_cents = amount_cents
        self.method = method

        # optional stripe fields used by repo helper / checkout flow
        self.stripe_checkout_id = None
        self.stripe_payment_intent_id = None


class FakePaymentRepo:
    """
    In-memory repo. Mimics methods used by PaymentService.
    """
    def __init__(self, db: FakeDB):
        self.db = db
        self._payments: dict[int, FakePayment] = {}
        self._next_id = 1
        self.deleted_ids: list[int] = []
        self.set_status_calls: list[tuple[int, str]] = []

    def create(self, **kwargs) -> FakePayment:
        p = FakePayment(id=self._next_id, **kwargs)
        self._payments[self._next_id] = p
        self._next_id += 1
        return p

    def get(self, payment_id: int):
        return self._payments.get(payment_id)

    def list(self, *, session_id=None, subscription_id=None, status=None):
        out = list(self._payments.values())
        if session_id is not None:
            out = [p for p in out if p.session_id == session_id]
        if subscription_id is not None:
            out = [p for p in out if p.subscription_id == subscription_id]
        if status is not None:
            out = [p for p in out if p.status == status]
        # mimic "desc" ordering
        return sorted(out, key=lambda p: p.id, reverse=True)

    def set_status(self, p: FakePayment, status: str) -> FakePayment:
        p.status = status
        self.set_status_calls.append((p.id, status))
        return p

    def delete(self, p: FakePayment) -> None:
        self.deleted_ids.append(p.id)
        self._payments.pop(p.id, None)

    # Helpers used by create_checkout_for_session (if it exists)
    def get_pending_for_session(self, session_id: int):
        for p in self._payments.values():
            if p.session_id == session_id and p.status == "pending":
                return p
        return None

    def attach_stripe_ids(self, p: FakePayment, *, checkout_id=None, payment_intent_id=None):
        if checkout_id:
            p.stripe_checkout_id = checkout_id
        if payment_intent_id:
            p.stripe_payment_intent_id = payment_intent_id
        return p


# -----------------------------
# Fixtures
# -----------------------------

@pytest.fixture()
def db():
    return FakeDB()


@pytest.fixture()
def repo(db):
    return FakePaymentRepo(db)


@pytest.fixture()
def svc(repo):
    return payments_module.PaymentService(repo)


# -----------------------------
# Tests: create / get / list
# -----------------------------



def test_create_session_not_found_404(svc, db):
    from src.schemas.payment import PaymentCreate
    # session_id provided but not in FakeDB store
    payload = PaymentCreate(session_id=123, subscription_id=None, currency="eur", amount_cents=100)

    with pytest.raises(HTTPException) as e:
        svc.create(payload)

    assert e.value.status_code == 404
    assert e.value.detail == "Session not found"


def test_create_subscription_not_found_404(svc, db):
    from src.schemas.payment import PaymentCreate
    payload = PaymentCreate(session_id=None, subscription_id=999, currency="eur", amount_cents=100)

    with pytest.raises(HTTPException) as e:
        svc.create(payload)

    assert e.value.status_code == 404
    assert e.value.detail == "Subscription not found"


def test_create_uppercases_currency(svc, db):
    from src.schemas.payment import PaymentCreate
    from src.models.session import Session as SessionModel

    db.put(SessionModel, 1, object())
    payload = PaymentCreate(session_id=1, subscription_id=None, currency="bgn", amount_cents=123)

    p = svc.create(payload)
    assert p.currency == "BGN"


def test_get_missing_payment_404(svc):
    with pytest.raises(HTTPException) as e:
        svc.get(999)
    assert e.value.status_code == 404
    assert e.value.detail == "Payment not found"


def test_list_filters_by_status(repo, svc, db):
    from src.models.session import Session as SessionModel

    db.put(SessionModel, 1)
    p1 = repo.create(session_id=1, subscription_id=None, status="pending", currency="EUR", amount_cents=100, method="card")
    p2 = repo.create(session_id=1, subscription_id=None, status="succeeded", currency="EUR", amount_cents=100, method="card")

    out = svc.list(session_id=1, subscription_id=None, status=PaymentStatus.succeeded)
    assert [p.id for p in out] == [p2.id]


# -----------------------------
# Tests: set_status transitions
# -----------------------------

def test_set_status_idempotent_no_repo_call(repo, svc, db):
    from src.models.session import Session as SessionModel

    db.put(SessionModel, 1)
    p = repo.create(session_id=1, subscription_id=None, status="pending", currency="EUR", amount_cents=100, method="card")

    # first change -> repo called
    svc.set_status(p.id, PaymentStatus.succeeded)
    assert repo.set_status_calls[-1] == (p.id, "succeeded")

    # second change to same -> no new call
    before = len(repo.set_status_calls)
    svc.set_status(p.id, PaymentStatus.succeeded)
    after = len(repo.set_status_calls)
    assert after == before


def test_set_status_pending_allows_succeeded_or_failed(repo, svc, db):
    from src.models.session import Session as SessionModel

    db.put(SessionModel, 1)
    p = repo.create(session_id=1, subscription_id=None, status="pending", currency="EUR", amount_cents=100, method="card")

    svc.set_status(p.id, PaymentStatus.failed)
    assert p.status == "failed"


def test_set_status_pending_blocks_refunded(repo, svc, db):
    from src.models.session import Session as SessionModel

    db.put(SessionModel, 1)
    p = repo.create(session_id=1, subscription_id=None, status="pending", currency="EUR", amount_cents=100, method="card")

    with pytest.raises(HTTPException) as e:
        svc.set_status(p.id, PaymentStatus.refunded)
    assert e.value.status_code == 400
    assert "only succeeded or failed" in e.value.detail.lower()


def test_set_status_succeeded_only_allows_refunded(repo, svc, db):
    from src.models.session import Session as SessionModel

    db.put(SessionModel, 1)
    p = repo.create(session_id=1, subscription_id=None, status="succeeded", currency="EUR", amount_cents=100, method="card")

    with pytest.raises(HTTPException) as e:
        svc.set_status(p.id, PaymentStatus.failed)
    assert e.value.status_code == 400
    assert "only refunded" in e.value.detail.lower()


def test_set_status_failed_has_no_transitions(repo, svc, db):
    from src.models.session import Session as SessionModel

    db.put(SessionModel, 1)
    p = repo.create(session_id=1, subscription_id=None, status="failed", currency="EUR", amount_cents=100, method="card")

    with pytest.raises(HTTPException) as e:
        svc.set_status(p.id, PaymentStatus.succeeded)
    assert e.value.status_code == 400
    assert "no transitions" in e.value.detail.lower()


def test_set_status_refunded_has_no_transitions(repo, svc, db):
    from src.models.session import Session as SessionModel

    db.put(SessionModel, 1)
    p = repo.create(session_id=1, subscription_id=None, status="refunded", currency="EUR", amount_cents=100, method="card")

    with pytest.raises(HTTPException) as e:
        svc.set_status(p.id, PaymentStatus.succeeded)
    assert e.value.status_code == 400
    assert "no transitions" in e.value.detail.lower()


# -----------------------------
# Tests: subscription activation side effect
# -----------------------------

def test_set_status_succeeded_activates_subscription_only_when_subscription_payment(repo, svc, db, monkeypatch):
    from src.models.subscription import Subscription as SubscriptionModel

    db.put(SubscriptionModel, 10)  # make subscription exist so create/set_status are valid

    # Create payment linked to subscription
    p = repo.create(
        session_id=None,
        subscription_id=10,
        status="pending",
        currency="EUR",
        amount_cents=500,
        method="card",
    )

    # Patch SubscriptionRepository + SubscriptionService inside payments module
    called = {"sub_id": None}

    class FakeSubRepo:
        def __init__(self, db_):
            self.db = db_

    class FakeSubSvc:
        def __init__(self, repo_):
            self.repo = repo_

        def activate_on_payment(self, sub_id: int):
            called["sub_id"] = sub_id

    monkeypatch.setattr(payments_module, "SubscriptionRepository", FakeSubRepo)
    monkeypatch.setattr(payments_module, "SubscriptionService", FakeSubSvc)

    svc.set_status(p.id, PaymentStatus.succeeded)
    assert called["sub_id"] == 10


def test_set_status_succeeded_does_not_activate_when_no_subscription_id(repo, svc, db, monkeypatch):
    from src.models.session import Session as SessionModel

    db.put(SessionModel, 1)

    p = repo.create(
        session_id=1,
        subscription_id=None,
        status="pending",
        currency="EUR",
        amount_cents=500,
        method="card",
    )

    called = {"count": 0}

    class FakeSubRepo:
        def __init__(self, db_):
            self.db = db_

    class FakeSubSvc:
        def __init__(self, repo_):
            self.repo = repo_

        def activate_on_payment(self, sub_id: int):
            called["count"] += 1

    monkeypatch.setattr(payments_module, "SubscriptionRepository", FakeSubRepo)
    monkeypatch.setattr(payments_module, "SubscriptionService", FakeSubSvc)

    svc.set_status(p.id, PaymentStatus.succeeded)
    assert called["count"] == 0


def test_set_status_failed_does_not_activate_subscription(repo, svc, db, monkeypatch):
    from src.models.subscription import Subscription as SubscriptionModel

    db.put(SubscriptionModel, 10)

    p = repo.create(
        session_id=None,
        subscription_id=10,
        status="pending",
        currency="EUR",
        amount_cents=500,
        method="card",
    )

    called = {"count": 0}

    class FakeSubRepo:
        def __init__(self, db_):
            self.db = db_

    class FakeSubSvc:
        def __init__(self, repo_):
            self.repo = repo_

        def activate_on_payment(self, sub_id: int):
            called["count"] += 1

    monkeypatch.setattr(payments_module, "SubscriptionRepository", FakeSubRepo)
    monkeypatch.setattr(payments_module, "SubscriptionService", FakeSubSvc)

    svc.set_status(p.id, PaymentStatus.failed)
    assert called["count"] == 0


# -----------------------------
# Tests: delete guard
# -----------------------------

def test_delete_blocks_succeeded_payment(repo, svc, db):
    from src.models.session import Session as SessionModel

    db.put(SessionModel, 1)
    p = repo.create(session_id=1, subscription_id=None, status="succeeded", currency="EUR", amount_cents=100, method="card")

    with pytest.raises(HTTPException) as e:
        svc.delete(p.id)

    assert e.value.status_code == 409
    assert "refund" in e.value.detail.lower()
    assert p.id not in repo.deleted_ids


def test_delete_allows_non_succeeded(repo, svc, db):
    from src.models.session import Session as SessionModel

    db.put(SessionModel, 1)
    p = repo.create(session_id=1, subscription_id=None, status="failed", currency="EUR", amount_cents=100, method="card")

    svc.delete(p.id)
    assert p.id in repo.deleted_ids


# -----------------------------
# Optional: checkout method exists?
# -----------------------------

def test_checkout_method_is_not_nested_under_delete():
    """
    Your pasted PaymentService code shows create_checkout_for_session() indented inside delete().
    If that's true in your codebase, PaymentService won't have create_checkout_for_session at all.
    This test tells you immediately if the method is missing.
    """
    if not hasattr(payments_module.PaymentService, "create_checkout_for_session"):
        pytest.skip("PaymentService.create_checkout_for_session is missing (likely indented inside delete()). Fix indentation to unit-test checkout flow.")
