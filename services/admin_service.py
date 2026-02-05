"""Admin-only management service."""
import sqlite3

from utils.errors import DatabaseError
from utils.security import hash_password
from utils.validators import require_text


class AdminService:
    def __init__(self, db, user_dao, zone_dao, auth_service):
        self.db = db
        self.user_dao = user_dao
        self.zone_dao = zone_dao
        self.auth_service = auth_service

    def list_zones(self):
        return self.zone_dao.list_zones()

    def add_zone(self, admin_user, zone_name):
        self.auth_service.ensure_role(admin_user, ["MunicipalAdmin"])
        zone_name = require_text(zone_name, "Zone name")
        try:
            return self.zone_dao.create_zone(zone_name)
        except sqlite3.Error as exc:
            print(f"[DB] add zone failure: {exc}")
            raise DatabaseError("Could not add zone.")

    def update_zone(self, admin_user, zone_id, zone_name):
        self.auth_service.ensure_role(admin_user, ["MunicipalAdmin"])
        zone_name = require_text(zone_name, "Zone name")
        try:
            self.zone_dao.update_zone(int(zone_id), zone_name)
        except sqlite3.Error as exc:
            print(f"[DB] update zone failure: {exc}")
            raise DatabaseError("Could not update zone.")

    def create_staff_user(self, admin_user, name, password, role, zone_id=None):
        self.auth_service.ensure_role(admin_user, ["MunicipalAdmin"])
        name = require_text(name, "Name")
        password = require_text(password, "Password")
        if role not in ("WasteCollector", "MunicipalAdmin"):
            raise ValueError("Admin can only create WasteCollector or MunicipalAdmin users.")
        try:
            zone = int(zone_id) if zone_id not in (None, "") else None
            return self.user_dao.create_user(name, hash_password(password), role, zone)
        except sqlite3.Error as exc:
            print(f"[DB] create user failure: {exc}")
            raise DatabaseError("Could not create user.")

    def update_user(self, admin_user, user_id, name=None, password=None, role=None, zone_id=None):
        self.auth_service.ensure_role(admin_user, ["MunicipalAdmin"])
        pwd_hash = hash_password(password) if (password or "").strip() else None
        if role and role not in ("Resident", "WasteCollector", "MunicipalAdmin"):
            raise ValueError("Invalid role.")

        try:
            if zone_id == "":
                with self.db.connect() as conn:
                    cur = conn.cursor()
                    cur.execute("UPDATE users SET zone_id=NULL WHERE user_id=?", (int(user_id),))
                    conn.commit()
                zid = None
            else:
                zid = int(zone_id) if zone_id is not None else None
            self.user_dao.update_user(int(user_id), name=name or None, password_hash=pwd_hash, role=role, zone_id=zid)
        except sqlite3.Error as exc:
            print(f"[DB] update user failure: {exc}")
            raise DatabaseError("Could not update user.")

    def list_users(self):
        return self.user_dao.list_users()

    def get_overview_counts(self, admin_user):
        self.auth_service.ensure_role(admin_user, ["MunicipalAdmin"])
        with self.db.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM users")
            users = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM pickup_request")
            pickups = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM recycling_log")
            logs = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM notification")
            notes = cur.fetchone()[0]
            return {
                "users": users,
                "pickup_requests": pickups,
                "recycling_logs": logs,
                "notifications": notes,
            }
