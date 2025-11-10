from typing import Optional
from sqlalchemy.orm import Session
from ..repositories.vehicle_sqlalchemy import VehicleRepository
from ..repositories.subscription_sqlalchemy import SubscriptionRepository
from ..models.audit import AuditEvent
from ..models.vehicle import Vehicle

class AccessListService:
    def __init__(self, db: Session):
        self.db = db
        self.vehicles = VehicleRepository(db)
        self.subs = SubscriptionRepository(db)

    def _audit(self, *, admin_id: int, vehicle_id: int, action: str, reason: Optional[str]) -> None:
        evt = AuditEvent(
            admin_id=admin_id, vehicle_id=vehicle_id, action=action, reason=reason or None
        )
        self.db.add(evt)
        self.db.commit()

    def blacklist(self, *, admin_id: int, vehicle_id: int, reason: Optional[str] = None) -> Vehicle:
        v = self.vehicles.set_blacklist(vehicle_id, True)
        if not v:
            raise ValueError("vehicle_not_found")

        # Hard-cancel any currently active subscriptions for that vehicle
        self.subs.cancel_all_active_for_vehicle(vehicle_id)

        self._audit(
            admin_id=admin_id, vehicle_id=vehicle_id, action="vehicle.blacklist", reason=reason
        )
        return v

    def whitelist(
        self,
        *,
        admin_id: int,
        vehicle_id: int,
        reason: Optional[str] = None,
        resume_suspended: bool = False,   # keep param for compatibility; keep default False
    ) -> Vehicle:
        v = self.vehicles.set_blacklist(vehicle_id, False)
        if not v:
            raise ValueError("vehicle_not_found")

        # IMPORTANT: do NOT auto-resume; leave vehicle "pending" until a plan is linked.
        if resume_suspended:
            # If you still want an escape hatch, allow explicit resume.
            self.subs.resume_all_for_vehicle(vehicle_id)

        self._audit(
            admin_id=admin_id, vehicle_id=vehicle_id, action="vehicle.whitelist", reason=reason
        )
        return v

    def delete_blacklisted(self, *, admin_id: int, vehicle_id: int, reason: str | None = None) -> None:
        v = self.vehicles.get_by_id(vehicle_id)
        if not v:
            raise ValueError("vehicle_not_found")
        if not v.is_blacklisted:
            raise ValueError("vehicle_not_blacklisted")

        #  audit first, while vehicle still exists
        self._audit(
            admin_id=admin_id,
            vehicle_id=vehicle_id,
            action="vehicle.delete_blacklisted",
            reason=reason,
        )

        ok = self.vehicles.delete_if_blacklisted(vehicle_id)
        if not ok:
            raise ValueError("delete_failed")
