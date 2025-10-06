from typing import Optional, Dict, Any
from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..repositories.plan_sqlalchemy import PlanRepository
from ..models.plan import Plan, PlanType
from ..schemas.plan import PlanCreate, PlanUpdate

class PlanService:
    def __init__(self, repo: PlanRepository):
        self.repo = repo
        self.db: Session = repo.db

    def _validate_combo(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Normalize currency uppercase if present
        if "currency" in data and data["currency"] is not None:
            data["currency"] = data["currency"].upper()

        type_ = data.get("type")
        ppc = data.get("period_price_cents")
        ppm = data.get("price_per_minute_cents")
        bp  = data.get("billing_period")

        if type_ == PlanType.subscription:
            if ppc is None or bp is None:
                raise HTTPException(status_code=400, detail="Subscription plans require period_price_cents and billing_period")
            # ppm optional
        elif type_ == PlanType.visitor:
            if ppm is None:
                raise HTTPException(status_code=400, detail="Visitor plans require price_per_minute_cents")
            if ppc is not None or bp is not None:
                raise HTTPException(status_code=400, detail="Visitor plans must not define period_price_cents or billing_period")
        else:
            raise HTTPException(status_code=400, detail="Invalid plan type")
        return data

    def create(self, payload: PlanCreate) -> Plan:
        data = payload.model_dump()
        data = self._validate_combo(data)
        return self.repo.create(**data)

    def get(self, plan_id: int) -> Plan:
        plan = self.repo.get(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        return plan

    def list(self, *, type_: Optional[PlanType]) -> list[Plan]:
        return self.repo.list(type_=type_)

    def update(self, plan_id: int, patch: PlanUpdate) -> Plan:
        plan = self.get(plan_id)

        # Merge existing values with patch to re-validate a complete view
        merged: Dict[str, Any] = {
            "type": plan.type,
            "currency": plan.currency,
            "period_price_cents": plan.period_price_cents,
            "price_per_minute_cents": plan.price_per_minute_cents,
            "billing_period": plan.billing_period,
            "method": plan.method,
        }
        for k, v in patch.model_dump(exclude_unset=True).items():
            merged[k] = v

        merged = self._validate_combo(merged)
        return self.repo.update(plan, **merged)

    def delete(self, plan_id: int) -> None:
        plan = self.get(plan_id)
        # Optional: add guard to prevent deleting a Plan referenced by active/pending subscriptions
        # if self.db.query(Subscription).filter_by(plan_id=plan_id).first():
        #     raise HTTPException(status_code=409, detail="Plan is in use by subscriptions")
        self.repo.delete(plan)
