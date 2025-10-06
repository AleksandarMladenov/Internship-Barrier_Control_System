from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class SessionBase(BaseModel):
    vehicle_id: int

class SessionCreate(SessionBase):
    # Optional override for start time; defaults to DB now()
    started_at: Optional[datetime] = Field(default=None)

class SessionEnd(BaseModel):
    # Optional explicit end time; default will be "now" in the service
    ended_at: Optional[datetime] = Field(default=None, description="UTC timestamp; defaults to now")

class SessionRead(SessionBase):
    id: int
    started_at: datetime
    ended_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
