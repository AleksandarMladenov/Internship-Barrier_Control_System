from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

class SubscriptionStatus(str, Enum):
    pending_payment = "pending_payment"
    active = "active"
    paused = "paused"
    canceled = "canceled"

class SubscriptionBase(BaseModel):
    vehicle_id: int
    plan_id: int
    auto_renew: bool = True
    valid_from: datetime
    valid_to: datetime

class SubscriptionCreate(SubscriptionBase):
    # Admin creates the record (this is the “approval”).
    # It starts as pending_payment until a successful payment arrives.
    pass

class SubscriptionRead(SubscriptionBase):
    id: int
    status: SubscriptionStatus
    model_config = {"from_attributes": True}

class SubscriptionStatusUpdate(BaseModel):
    status: SubscriptionStatus = Field(description="active | paused | canceled")
    auto_renew: bool | None = None  # optional toggle when changing status

# Optional: tiny schema for payment webhooks / internal calls
class SubscriptionActivateOnPayment(BaseModel):
    payment_id: int
