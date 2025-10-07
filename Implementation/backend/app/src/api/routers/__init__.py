from fastapi import APIRouter
from . import admins, drivers, payments, plans, sessions, subscriptions, vehicles
from . import scans  # <- make sure this exists

api_router = APIRouter()
api_router.include_router(admins.router)
api_router.include_router(drivers.router)
api_router.include_router(payments.router)
api_router.include_router(plans.router)
api_router.include_router(sessions.router)
api_router.include_router(subscriptions.router)
api_router.include_router(vehicles.router)
api_router.include_router(scans.router)  # <- include scans
