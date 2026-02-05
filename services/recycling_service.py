"""Recycling log and points calculation service."""
import sqlite3

from utils.errors import DatabaseError
from utils.validators import require_positive_number, require_text
from utils.time_utils import now_iso


class RecyclingService:
    def __init__(self, db, recycling_dao, user_dao, auth_service):
        self.db = db
        self.recycling_dao = recycling_dao
        self.user_dao = user_dao
        self.auth_service = auth_service

    def submit_recycling_log(self, resident_user, category, weight_kg, waste_image=None):
        """Stores recycling log and adds points transactionally."""
        self.auth_service.ensure_role(resident_user, ["Resident"])
        category = require_text(category, "Category")
        weight = require_positive_number(weight_kg, "Weight")
        points_added = int(weight * 10)

        try:
            with self.db.connect() as conn:
                self.recycling_dao.create_log(
                    conn,
                    resident_user["user_id"],
                    category,
                    weight,
                    now_iso(),
                    (waste_image or "").strip() or None,
                )
                self.user_dao.add_points(conn, resident_user["user_id"], points_added)
                conn.commit()
            return points_added
        except sqlite3.Error as exc:
            print(f"[DB] submit recycling failure: {exc}")
            raise DatabaseError("Could not submit recycling log.")

    def get_history(self, resident_user):
        self.auth_service.ensure_role(resident_user, ["Resident"])
        return self.recycling_dao.list_by_resident(resident_user["user_id"])
