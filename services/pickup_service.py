"""Pickup request business rules."""
import sqlite3

from utils.errors import AuthorizationError, DatabaseError, NotFoundError, ValidationError
from utils.time_utils import now_iso
from utils.validators import require_text


class PickupService:
    def __init__(self, db, pickup_dao, status_dao, auth_service):
        self.db = db
        self.pickup_dao = pickup_dao
        self.status_dao = status_dao
        self.auth_service = auth_service

    def create_pickup_request(self, resident_user, requested_datetime):
        """Create a pickup request for resident zone with initial PENDING status."""
        self.auth_service.ensure_role(resident_user, ["Resident"])
        dt = require_text(requested_datetime, "Requested datetime")
        zone_id = resident_user["zone_id"]
        if zone_id is None:
            raise ValidationError("Cannot create pickup request: no zone assigned. Contact admin.")
        try:
            return self.pickup_dao.create_request(resident_user["user_id"], zone_id, dt, "PENDING")
        except sqlite3.Error as exc:
            print(f"[DB] create pickup failure: {exc}")
            raise DatabaseError("Could not create pickup request.")

    def get_resident_requests(self, resident_user):
        self.auth_service.ensure_role(resident_user, ["Resident"])
        return self.pickup_dao.list_by_resident(resident_user["user_id"])

    def get_collector_requests(self, collector_user):
        self.auth_service.ensure_role(collector_user, ["WasteCollector"])
        if collector_user["zone_id"] is None:
            raise ValidationError("Collector has no zone assigned.")
        return self.pickup_dao.list_by_zone(collector_user["zone_id"])

    def update_pickup_status(self, collector_user, pickup_id, new_status, comment=None, evidence_image=None):
        """Collector updates pickup status with history record transactionally."""
        self.auth_service.ensure_role(collector_user, ["WasteCollector"])
        if new_status not in ("COMPLETED", "FAILED"):
            raise ValidationError("Status must be COMPLETED or FAILED.")
        if new_status == "FAILED" and not (comment or "").strip():
            raise ValidationError("Failed pickup requires a comment.")

        pickup = self.pickup_dao.get_by_id(int(pickup_id))
        if not pickup:
            raise NotFoundError("Pickup request not found.")
        if collector_user["zone_id"] != pickup["zone_id"]:
            raise AuthorizationError("Cannot update request outside your zone.")

        try:
            with self.db.connect() as conn:
                self.pickup_dao.update_status(conn, pickup["pickup_id"], new_status)
                self.status_dao.create_update(
                    conn,
                    pickup["pickup_id"],
                    collector_user["user_id"],
                    new_status,
                    now_iso(),
                    (comment or "").strip() or None,
                    (evidence_image or "").strip() or None,
                )
                conn.commit()
        except sqlite3.Error as exc:
            print(f"[DB] update pickup status failure: {exc}")
            raise DatabaseError("Could not update pickup status.")

    def get_status_history(self, pickup_id):
        return self.status_dao.list_by_pickup(int(pickup_id))
