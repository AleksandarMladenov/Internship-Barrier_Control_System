from math import ceil
from datetime import datetime

def billable_minutes(started_at: datetime, now: datetime, grace_min: int, round_up: bool) -> int:
    total = max(0.0, (now - started_at).total_seconds() / 60.0)
    billable = max(0.0, total - grace_min)
    return int(ceil(billable) if round_up else int(billable))

def compute_amount_cents(started_at: datetime, now: datetime, price_per_minute_cents: int,
                         grace_min: int, round_up: bool) -> tuple[int, int]:
    mins = billable_minutes(started_at, now, grace_min, round_up)
    return mins * int(price_per_minute_cents), mins
