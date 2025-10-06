from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..deps import get_plan_service
from ...schemas.plan import PlanCreate, PlanRead, PlanUpdate, PlanType
from ...services.plans import PlanService

router = APIRouter(prefix="/plans", tags=["plans"])

@router.post("", response_model=PlanRead, status_code=201)
def create_plan(
    payload: PlanCreate,
    svc: PlanService = Depends(get_plan_service),
):
    return svc.create(payload)

@router.get("/{plan_id}", response_model=PlanRead)
def get_plan(
    plan_id: int,
    svc: PlanService = Depends(get_plan_service),
):
    return svc.get(plan_id)

@router.get("", response_model=list[PlanRead])
def list_plans(
    type: Optional[PlanType] = Query(default=None, description="Filter by type (subscription | visitor)"),
    svc: PlanService = Depends(get_plan_service),
):
    return svc.list(type_=type)

@router.patch("/{plan_id}", response_model=PlanRead)
def update_plan(
    plan_id: int,
    payload: PlanUpdate,
    svc: PlanService = Depends(get_plan_service),
):
    return svc.update(plan_id, payload)

@router.delete("/{plan_id}", status_code=204)
def delete_plan(
    plan_id: int,
    svc: PlanService = Depends(get_plan_service),
):
    svc.delete(plan_id)
