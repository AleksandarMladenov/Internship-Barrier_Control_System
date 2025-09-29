from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.types import Numeric
import enum
from .base import Base

class PlanType(str, enum.Enum):
    subscription = "subscription"
    visitor = "visitor"

class BillingPeriod(str, enum.Enum):
    month = "month"
    week = "week"
    day = "day"

class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum(PlanType), nullable=False)  # From ERD: Type (Sub, Visitor…)
    currency = Column(String(3), nullable=False)   # ISO-4217 like "EUR"
    period_price_cents = Column(Integer, nullable=True)        # for subscriptions
    price_per_minute_cents = Column(Integer, nullable=True)    # for visitor/overage
    billing_period = Column(Enum(BillingPeriod), nullable=True) # if subscription
    method = Column(String(32), nullable=True) # e.g., "card", "cash" (as shown in ERD)
