from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, model_validator

class PlanType(str, Enum):
    subscription = "subscription"
    visitor = "visitor"

class BillingPeriod(str, Enum):
    month = "month"
    year = "year"

class PlanBase(BaseModel):
    type: PlanType
    currency: str = Field(min_length=3, max_length=3, description="ISO-4217 uppercase, e.g. EUR")
    period_price_cents: Optional[int] = Field(default=None, ge=0)
    price_per_minute_cents: Optional[int] = Field(default=None, ge=0)
    billing_period: Optional[BillingPeriod] = None
    method: Optional[str] = Field(default=None, max_length=32)

    @model_validator(mode="after")
    def validate_combo(self):

        self.currency = self.currency.upper()

        if self.type == PlanType.subscription:
            if self.period_price_cents is None or self.billing_period is None:
                raise ValueError("Subscription plans require period_price_cents and billing_period")

        else:  # visitor
            if self.price_per_minute_cents is None:
                raise ValueError("Visitor plans require price_per_minute_cents")
            if self.period_price_cents is not None or self.billing_period is not None:
                raise ValueError("Visitor plans must not set period_price_cents or billing_period")
        return self

class PlanCreate(PlanBase):
    pass

class PlanUpdate(BaseModel):

    type: Optional[PlanType] = None
    currency: Optional[str] = Field(default=None, min_length=3, max_length=3)
    period_price_cents: Optional[int] = Field(default=None, ge=0)
    price_per_minute_cents: Optional[int] = Field(default=None, ge=0)
    billing_period: Optional[BillingPeriod] = None
    method: Optional[str] = Field(default=None, max_length=32)

class PlanRead(PlanBase):
    id: int
    model_config = {"from_attributes": True}
