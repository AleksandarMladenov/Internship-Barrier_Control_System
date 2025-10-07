# backend/app/src/schemas/scan.py
from datetime import datetime
from pydantic import BaseModel, Field

class EntryScanRequest(BaseModel):
    region_code: str = Field(..., min_length=1, max_length=10)
    plate_text: str = Field(..., min_length=2, max_length=16)
    gate_id: str | None = None
    source: str | None = None

class EntryScanResponse(BaseModel):
    session_id: int
    status: str                 # "open" | "denied"
    reason: str | None = None   # "created" | "existing_open_session" | "blacklisted" | "not_allowed"
    barrier_action: str | None = None  # "open" | "hold"
    created_at_utc: datetime | None = None

    model_config = {"from_attributes": True}
