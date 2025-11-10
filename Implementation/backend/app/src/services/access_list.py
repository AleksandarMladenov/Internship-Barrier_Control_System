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
        evt = AuditEvent(admin_id=admin_id, vehicle_id=vehicle_id, action=action, reason=reason or None)
        self.db.add(evt)
        self.db.commit()

    def blacklist(self, *, admin_id: int, vehicle_id: int, reason: Optional[str] = None) -> Vehicle:
        v = self.vehicles.set_blacklist(vehicle_id, True)
        if not v:
            raise ValueError("vehicle_not_found")
        # suspend all active subs for that vehicle
        self.subs.suspend_all_for_vehicle(vehicle_id)
        self._audit(admin_id=admin_id, vehicle_id=vehicle_id, action="vehicle.blacklist", reason=reason)
        return v

    def whitelist(self, *, admin_id: int, vehicle_id: int, reason: Optional[str] = None, resume_suspended: bool = False) -> Vehicle:
        v = self.vehicles.set_blacklist(vehicle_id, False)
        if not v:
            raise ValueError("vehicle_not_found")
        #  policy: decide whether to resume previously suspended subs automatically
        if resume_suspended:
            self.subs.resume_all_for_vehicle(vehicle_id)
        self._audit(admin_id=admin_id, vehicle_id=vehicle_id, action="vehicle.whitelist", reason=reason)
        return v

    def delete_blacklisted(self, *, admin_id: int, vehicle_id: int, reason: str | None = None) -> None:
        # only allow delete when currently blacklisted
        v = self.vehicles.get_by_id(vehicle_id)
        if not v:
            raise ValueError("vehicle_not_found")
        if not v.is_blacklisted:
            raise ValueError("vehicle_not_blacklisted")

        # (Already suspended subs on blacklist; delete will cascade)
        ok = self.vehicles.delete_if_blacklisted(vehicle_id)
        if not ok:
            raise ValueError("delete_failed")

        self._audit(admin_id=admin_id, vehicle_id=vehicle_id, action="vehicle.delete_blacklisted", reason=reason)
