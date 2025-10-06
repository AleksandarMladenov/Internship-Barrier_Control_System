from typing import Optional, List
from sqlalchemy.orm import Session
from ..models.plan import Plan, PlanType

class PlanRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs) -> Plan:
        plan = Plan(**kwargs)
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def get(self, plan_id: int) -> Optional[Plan]:
        return self.db.get(Plan, plan_id)

    def list(self, *, type_: Optional[PlanType] = None) -> List[Plan]:
        q = self.db.query(Plan)
        if type_ is not None:
            q = q.filter(Plan.type == type_)
        return q.order_by(Plan.id.desc()).all()

    def update(self, plan: Plan, **kwargs) -> Plan:
        for k, v in kwargs.items():
            setattr(plan, k, v)
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def delete(self, plan: Plan) -> None:
        self.db.delete(plan)
        self.db.commit()
