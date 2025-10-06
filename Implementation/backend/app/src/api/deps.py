from sqlalchemy.orm import Session
from fastapi import Depends

from ..db.database import SessionLocal
from ..repositories.admin_sqlalchemy import AdminRepository
from ..repositories.subscription_sqlalchemy import SubscriptionRepository
from ..repositories.vehicle_sqlalchemy import VehicleRepository
from ..services.subscriptions import SubscriptionService
from ..services.vehicles import VehicleService
from ..repositories.driver_sqlalchemy import DriverRepository
from ..services.drivers import DriverService
from ..services.admins import AdminService
from ..repositories.plan_sqlalchemy import PlanRepository
from ..services.plans import PlanService
from ..repositories.session_sqlalchemy import ParkingSessionRepository
from ..services.sessions import ParkingSessionService
from ..repositories.payment_sqlalchemy import PaymentRepository
from ..services.payments import PaymentService


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_vehicle_service(db: Session = Depends(get_db)) -> VehicleService:
    repo = VehicleRepository(db)
    return VehicleService(repo)

def get_driver_service(db: Session = Depends(get_db)) -> DriverService:
    repo = DriverRepository(db)
    return DriverService(repo)

def get_admin_service(db: Session = Depends(get_db)) -> AdminService:
    repo = AdminRepository(db)
    return AdminService(repo)

def get_subscription_service(db: Session = Depends(get_db)) -> SubscriptionService:
    repo = SubscriptionRepository(db)
    return SubscriptionService(repo)

def get_plan_service(db: Session = Depends(get_db)) -> PlanService:
    repo = PlanRepository(db)
    return PlanService(repo)

def get_session_service(db: Session = Depends(get_db)) -> ParkingSessionService:
    repo = ParkingSessionRepository(db)
    return ParkingSessionService(repo)

def get_payment_service(db: Session = Depends(get_db)) -> PaymentService:
    repo = PaymentRepository(db)
    return PaymentService(repo)
