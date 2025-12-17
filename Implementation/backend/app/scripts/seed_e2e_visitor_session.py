from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from src.db.database import SessionLocal
from src.models.plan import Plan, PlanType
from src.models.vehicle import Vehicle
from src.models.session import Session as ParkingSession
from src.models.driver import Driver   # 👈 add this


def seed():
    db: Session = SessionLocal()

    try:
        # 1) Get or create VISITOR plan
        plan = db.query(Plan).filter(Plan.type == PlanType.visitor).first()
        if not plan:
            plan = Plan(
                type=PlanType.visitor,
                currency="EUR",
                price_per_minute_cents=5,
                method="card",
            )
            db.add(plan)
            db.commit()
            db.refresh(plan)

        # 2) Get or create a driver (required for Vehicle.driver_id NOT NULL)
        driver = db.query(Driver).filter(Driver.email == "e2e-visitor@local.test").first()
        if not driver:
            driver = Driver(name="E2E Visitor", email="e2e-visitor@local.test")
            db.add(driver)
            db.commit()
            db.refresh(driver)

        # 3) Create vehicle linked to driver
        vehicle = Vehicle(
            driver_id=driver.id,
            region_code="BG",
            plate_text="E2ETEST",
            is_blacklisted=False,
        )
        db.add(vehicle)
        db.commit()
        db.refresh(vehicle)

        # 4) Create CLOSED session
        started = datetime.now(timezone.utc) - timedelta(minutes=42)
        ended = datetime.now(timezone.utc)

        session = ParkingSession(
            vehicle_id=vehicle.id,
            plan_id=plan.id,
            started_at=started,
            ended_at=ended,
            duration=42,
            amount_charged=42 * plan.price_per_minute_cents,
            status="closed",
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        print("\n✅ Visitor session seeded successfully")
        print(f"Session ID: {session.id}")
        print(f"Plate: {vehicle.region_code}{vehicle.plate_text}")
        print(f"Amount: {session.amount_charged} cents\n")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
