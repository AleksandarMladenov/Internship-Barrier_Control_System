from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, model_validator

class PaymentStatus(str, Enum):
    pending = "pending"
    succeeded = "succeeded"
    failed = "failed"
    refunded = "refunded"

class PaymentBase(BaseModel):
    session_id: Optional[int] = None
    subscription_id: Optional[int] = None
    currency: str = Field(min_length=3, max_length=3, description="ISO-4217 code, e.g. EUR")
    amount_cents: int = Field(ge=1)
    method: Optional[str] = Field(default=None, max_length=32)

    @model_validator(mode="after")
    def xor_refs(self):
        if bool(self.session_id) == bool(self.subscription_id):
            # both set or both None
            raise ValueError("Exactly one of session_id or subscription_id must be provided")
        self.currency = self.currency.upper()
        return self

class PaymentCreate(PaymentBase):
    pass

class PaymentRead(PaymentBase):
    id: int
    status: PaymentStatus
    # created_at comes from DB default; we can expose it if desired
    # created_at: datetime
    model_config = {"from_attributes": True}

class PaymentUpdateStatus(BaseModel):
    status: PaymentStatus = Field(description="succeeded | failed | refunded")
