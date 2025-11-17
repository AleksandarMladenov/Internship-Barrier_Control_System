# app/src/schemas/session.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class VehicleStub(BaseModel):
    region_code: Optional[str] = None
    plate_text: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)   # <-- v2 way

class PlanStub(BaseModel):
    currency: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)   # <-- v2 way


class SessionBase(BaseModel):
    vehicle_id: int

class SessionCreate(SessionBase):
    started_at: Optional[datetime] = Field(default=None)

class SessionEnd(BaseModel):
    ended_at: Optional[datetime] = Field(default=None, description="UTC timestamp; defaults to now")


class SessionRead(SessionBase):
    id: int
    started_at: datetime
    ended_at: Optional[datetime] = None

    status: Optional[str] = None
    duration: Optional[int] = None
    amount_charged: Optional[int] = None

    vehicle: Optional[VehicleStub] = None
    plan: Optional[PlanStub] = None

    model_config = ConfigDict(from_attributes=True)   # <-- v2 way
