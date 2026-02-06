"""SQLite data access layer for Smart Waste desktop demo prototype."""
from __future__ import annotations

import logging
import shutil
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from utils.security import hash_password, verify_password

logger = logging.getLogger(__name__)

CATEGORY_MULTIPLIERS = {
    "Plastic": 2,
    "Paper": 1,
    "Glass": 2,
    "Metal": 3,
    "E-Waste": 4,
    "Organic": 1,
    "Other": 1,
}


class SQLiteService:
    LOCK_MINUTES = 10

    def __init__(self, path: str = "db/prototype.db"):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        try:
            self.conn = sqlite3.connect(path)
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA foreign_keys = ON")
            self._init_schema()
            self._apply_migrations()
            self._seed_data()
        except sqlite3.DatabaseError as exc:
            self._backup_corrupt_db()
            logger.exception("Database initialization failed")
            raise ValueError(
                "Database failed to initialize. Please restore from backup and restart."
            ) from exc

    @contextmanager
    def transaction(self):
        try:
            self.conn.execute("BEGIN")
            yield
            self.conn.commit()
        except sqlite3.DatabaseError:
            self.conn.rollback()
            logger.exception("Database transaction failed")
            raise

    def _table_columns(self, table: str) -> set[str]:
        rows = self.conn.execute(f"PRAGMA table_info({table})").fetchall()
        return {row["name"] for row in rows}

    def _init_schema(self):
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS zone (
                zone_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_login_id TEXT UNIQUE,
                user_id TEXT UNIQUE,
                name TEXT,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('Resident','WasteCollector','MunicipalAdmin')),
                zone_id INTEGER REFERENCES zone(zone_id),
                total_points INTEGER NOT NULL DEFAULT 0,
                email TEXT UNIQUE,
                phone TEXT,
                passport_no TEXT,
                address TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                failed_attempts INTEGER NOT NULL DEFAULT 0,
                locked_until TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS pickup_request (
                pickup_id INTEGER PRIMARY KEY AUTOINCREMENT,
                resident_id TEXT NOT NULL REFERENCES users(user_login_id),
                zone_id INTEGER NOT NULL REFERENCES zone(zone_id),
                requested_datetime TEXT NOT NULL,
                current_status TEXT NOT NULL DEFAULT 'PENDING' CHECK(current_status IN ('PENDING','ACCEPTED','IN_PROGRESS','COMPLETED','FAILED','CANCELLED')),
                cancelled_reason TEXT,
                points_awarded INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_update TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS pickup_status_update (
                status_update_id INTEGER PRIMARY KEY AUTOINCREMENT,
                pickup_id INTEGER NOT NULL REFERENCES pickup_request(pickup_id) ON DELETE CASCADE,
                updated_by TEXT REFERENCES users(user_login_id),
                new_status TEXT NOT NULL CHECK(new_status IN ('PENDING','ACCEPTED','IN_PROGRESS','COMPLETED','FAILED','CANCELLED')),
                timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                comment TEXT,
                evidence_image TEXT
            );

            CREATE TABLE IF NOT EXISTS recycling_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                pickup_id INTEGER UNIQUE REFERENCES pickup_request(pickup_id) ON DELETE CASCADE,
                resident_id TEXT NOT NULL REFERENCES users(user_login_id) ON DELETE CASCADE,
                category TEXT NOT NULL,
                weight_kg REAL NOT NULL,
                waste_image TEXT,
                points_added INTEGER NOT NULL DEFAULT 0,
                logged_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS notification (
                notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL REFERENCES users(user_login_id) ON DELETE CASCADE,
                type TEXT NOT NULL CHECK(type IN ('PICKUP_REMINDER','RECYCLING_TIP','STATUS_UPDATE','SYSTEM')),
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                read_at TEXT
            );
            """
        )
        self.conn.commit()

    def _apply_migrations(self):
        user_cols = self._table_columns("users")
        if "user_login_id" not in user_cols:
            self.conn.execute("ALTER TABLE users ADD COLUMN user_login_id TEXT")
            self.conn.execute("UPDATE users SET user_login_id = user_id WHERE user_login_id IS NULL")
        if "is_active" not in user_cols:
            self.conn.execute("ALTER TABLE users ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1")

        pickup_cols = self._table_columns("pickup_request")
        if "current_status" not in pickup_cols:
            self.conn.execute("ALTER TABLE pickup_request ADD COLUMN current_status TEXT DEFAULT 'PENDING'")
            self.conn.execute("UPDATE pickup_request SET current_status = COALESCE(status, 'PENDING')")
        if "cancelled_reason" not in pickup_cols:
            self.conn.execute("ALTER TABLE pickup_request ADD COLUMN cancelled_reason TEXT")
        if "points_awarded" not in pickup_cols:
            self.conn.execute("ALTER TABLE pickup_request ADD COLUMN points_awarded INTEGER NOT NULL DEFAULT 0")
        if "last_update" not in pickup_cols:
            self.conn.execute("ALTER TABLE pickup_request ADD COLUMN last_update TEXT DEFAULT CURRENT_TIMESTAMP")

        recycle_cols = self._table_columns("recycling_log")
        if "pickup_id" not in recycle_cols:
            self.conn.execute("ALTER TABLE recycling_log ADD COLUMN pickup_id INTEGER")

        status_cols = self._table_columns("pickup_status_update")
        if "updated_by" not in status_cols and "collector_id" in status_cols:
            self.conn.execute("ALTER TABLE pickup_status_update ADD COLUMN updated_by TEXT")
            self.conn.execute("UPDATE pickup_status_update SET updated_by = collector_id")

        self.conn.commit()

    def _backup_corrupt_db(self):
        src = Path(self.path)
        if src.exists():
            backup = src.with_suffix(f".corrupt-{datetime.now().strftime('%Y%m%d%H%M%S')}.db")
            shutil.copy2(src, backup)

    def _seed_data(self):
        for name in ("Zone A", "Zone B"):
            self.conn.execute("INSERT OR IGNORE INTO zone(name) VALUES(?)", (name,))
        zone_a = self.get_zone_id_by_name("Zone A")

        self.conn.execute(
            """INSERT OR IGNORE INTO users(user_login_id,user_id,name,password_hash,role,zone_id)
               VALUES(?,?,?,?,?,?)""",
            ("admin01", "admin01", "Municipal Admin", hash_password("Admin@1234"), "MunicipalAdmin", zone_a),
        )
        self.conn.execute(
            """INSERT OR IGNORE INTO users(user_login_id,user_id,name,password_hash,role,zone_id)
               VALUES(?,?,?,?,?,?)""",
            ("collector01", "collector01", "Collector One", hash_password("Collector@1234"), "WasteCollector", zone_a),
        )
        self.conn.commit()

    def get_zone_id_by_name(self, name: str):
        row = self.conn.execute("SELECT zone_id FROM zone WHERE name=?", (name,)).fetchone()
        return row["zone_id"] if row else None

    # auth + registration
    def create_basic_user(self, user_id: str, password: str):
        try:
            self.conn.execute(
                "INSERT INTO users(user_login_id,user_id,password_hash,role) VALUES(?,?,?,'Resident')",
                (user_id, user_id, hash_password(password)),
            )
            self.conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError("error_duplicate_user") from exc

    def complete_profile(self, data: dict):
        zone_id = self.get_zone_id_by_name(data["zone"])
        cur = self.conn.execute(
            """UPDATE users SET name=?,passport_no=?,phone=?,email=?,zone_id=?,address=?
               WHERE user_login_id=?""",
            (
                data["full_name"],
                data["id_no"],
                data["telephone"],
                data["email"].lower(),
                zone_id,
                data.get("address", ""),
                data["user_id"],
            ),
        )
        if cur.rowcount == 0:
            raise ValueError("Registration session expired. Please start again.")
        self.conn.commit()

    def verify_credentials(self, user_id: str, password: str):
        user = self.conn.execute(
            "SELECT user_login_id,password_hash,failed_attempts,locked_until,is_active FROM users WHERE user_login_id=?",
            (user_id,),
        ).fetchone()
        if not user or user["is_active"] == 0:
            return False, "invalid"
        if user["locked_until"]:
            locked = self.conn.execute("SELECT datetime('now') < datetime(?) AS y", (user["locked_until"],)).fetchone()["y"]
            if locked:
                return False, "locked"
        if verify_password(password, user["password_hash"]):
            self.conn.execute("UPDATE users SET failed_attempts=0,locked_until=NULL WHERE user_login_id=?", (user_id,))
            self.conn.commit()
            return True, user_id
        attempts = user["failed_attempts"] + 1
        if attempts >= 5:
            self.conn.execute("UPDATE users SET failed_attempts=?,locked_until=datetime('now','+10 minutes') WHERE user_login_id=?", (attempts, user_id))
        else:
            self.conn.execute("UPDATE users SET failed_attempts=? WHERE user_login_id=?", (attempts, user_id))
        self.conn.commit()
        return False, f"attempts_left:{max(0, 5-attempts)}"

    def get_user(self, user_id: str):
        return self.conn.execute(
            """SELECT u.*,z.name AS zone_name FROM users u
               LEFT JOIN zone z ON z.zone_id=u.zone_id WHERE u.user_login_id=?""",
            (user_id,),
        ).fetchone()

    # resident
    def create_pickup_with_recycling(self, resident_id: str, requested_datetime: str, category: str, weight_kg: float, image_path: str = ""):
        user = self.get_user(resident_id)
        if not user or not user["zone_id"]:
            raise ValueError("Resident zone is not configured.")
        with self.transaction():
            cur = self.conn.execute(
                "INSERT INTO pickup_request(resident_id,zone_id,requested_datetime,current_status) VALUES(?,?,?,'PENDING')",
                (resident_id, user["zone_id"], requested_datetime),
            )
            pickup_id = cur.lastrowid
            self.conn.execute(
                "INSERT INTO recycling_log(pickup_id,resident_id,category,weight_kg,waste_image) VALUES(?,?,?,?,?)",
                (pickup_id, resident_id, category, weight_kg, image_path),
            )
            self.conn.execute(
                "INSERT INTO pickup_status_update(pickup_id,updated_by,new_status,comment) VALUES(?,?,?,?)",
                (pickup_id, resident_id, "PENDING", "Pickup request submitted"),
            )
            self.add_notification(resident_id, "STATUS_UPDATE", "Pickup submitted", f"Pickup request #{pickup_id} submitted.")
        return pickup_id

    def list_resident_pickups(self, resident_id: str):
        return self.conn.execute(
            """SELECT p.pickup_id,z.name AS zone,p.requested_datetime,p.current_status,p.last_update,p.points_awarded
               FROM pickup_request p JOIN zone z ON z.zone_id=p.zone_id
               WHERE p.resident_id=? ORDER BY p.requested_datetime DESC""",
            (resident_id,),
        ).fetchall()

    def cancel_resident_pickup(self, resident_id: str, pickup_id: int, reason: str):
        row = self.conn.execute("SELECT current_status FROM pickup_request WHERE pickup_id=? AND resident_id=?", (pickup_id, resident_id)).fetchone()
        if not row:
            raise ValueError("Pickup not found.")
        if row["current_status"] not in ("PENDING", "ACCEPTED"):
            raise ValueError("Only pending/accepted pickups can be cancelled.")
        self._set_pickup_status(pickup_id, "CANCELLED", resident_id, reason)

    # collector
    def list_collector_tasks(self, collector_id: str):
        collector = self.get_user(collector_id)
        return self.conn.execute(
            """SELECT p.pickup_id,p.resident_id,p.requested_datetime,p.current_status,z.name AS zone
               FROM pickup_request p JOIN zone z ON z.zone_id=p.zone_id
               WHERE p.zone_id=? AND p.current_status IN ('PENDING','ACCEPTED','IN_PROGRESS')
               ORDER BY p.requested_datetime""",
            (collector["zone_id"],),
        ).fetchall()

    def collector_update_pickup(self, collector_id: str, pickup_id: int, new_status: str, comment: str = "", evidence_image: str = ""):
        if new_status in ("FAILED", "CANCELLED") and len(comment.strip()) < 5:
            raise ValueError("Comment/reason must be at least 5 characters.")
        self._set_pickup_status(pickup_id, new_status, collector_id, comment, evidence_image)

    def _set_pickup_status(self, pickup_id: int, new_status: str, updated_by: str, comment: str = "", evidence_image: str = ""):
        with self.transaction():
            self.conn.execute(
                "UPDATE pickup_request SET current_status=?,last_update=CURRENT_TIMESTAMP,cancelled_reason=CASE WHEN ?='CANCELLED' THEN ? ELSE cancelled_reason END WHERE pickup_id=?",
                (new_status, new_status, comment, pickup_id),
            )
            self.conn.execute(
                "INSERT INTO pickup_status_update(pickup_id,updated_by,new_status,comment,evidence_image) VALUES(?,?,?,?,?)",
                (pickup_id, updated_by, new_status, comment, evidence_image),
            )
            pickup = self.conn.execute("SELECT pickup_id,resident_id FROM pickup_request WHERE pickup_id=?", (pickup_id,)).fetchone()
            self.add_notification(pickup["resident_id"], "STATUS_UPDATE", "Pickup status updated", f"Pickup #{pickup_id} status updated to {new_status}.")
            admin_ids = [r["user_login_id"] for r in self.conn.execute("SELECT user_login_id FROM users WHERE role='MunicipalAdmin' AND is_active=1")]
            for aid in admin_ids:
                self.add_notification(aid, "SYSTEM", "Collector update", f"Pickup #{pickup_id} updated to {new_status}")
            if new_status == "COMPLETED":
                self._award_points_for_pickup(pickup_id)

    def _award_points_for_pickup(self, pickup_id: int):
        row = self.conn.execute("SELECT p.resident_id,r.category,r.weight_kg FROM pickup_request p JOIN recycling_log r ON r.pickup_id=p.pickup_id WHERE p.pickup_id=?", (pickup_id,)).fetchone()
        points = int(row["weight_kg"] * CATEGORY_MULTIPLIERS.get(row["category"], 1))
        self.conn.execute("UPDATE pickup_request SET points_awarded=? WHERE pickup_id=?", (points, pickup_id))
        self.conn.execute("UPDATE recycling_log SET points_added=? WHERE pickup_id=?", (points, pickup_id))
        self.conn.execute("UPDATE users SET total_points=total_points+? WHERE user_login_id=?", (points, row["resident_id"]))

    # notifications/admin/dashboard
    def add_notification(self, user_id: str, note_type: str, title: str, message: str):
        self.conn.execute("INSERT INTO notification(user_id,type,title,message) VALUES(?,?,?,?)", (user_id, note_type, title, message))

    def get_notifications(self, user_id: str):
        return self.conn.execute("SELECT * FROM notification WHERE user_id=? ORDER BY created_at DESC", (user_id,)).fetchall()

    def get_resident_stats(self, user_id: str):
        total = self.conn.execute("SELECT COUNT(*) c FROM pickup_request WHERE resident_id=?", (user_id,)).fetchone()["c"]
        completed = self.conn.execute("SELECT COUNT(*) c FROM pickup_request WHERE resident_id=? AND current_status='COMPLETED'", (user_id,)).fetchone()["c"]
        cancelled = self.conn.execute("SELECT COUNT(*) c FROM pickup_request WHERE resident_id=? AND current_status='CANCELLED'", (user_id,)).fetchone()["c"]
        failed = self.conn.execute("SELECT COUNT(*) c FROM pickup_request WHERE resident_id=? AND current_status='FAILED'", (user_id,)).fetchone()["c"]
        weight = self.conn.execute(
            """SELECT COALESCE(SUM(r.weight_kg),0) c FROM recycling_log r JOIN pickup_request p ON p.pickup_id=r.pickup_id
               WHERE p.resident_id=? AND p.current_status='COMPLETED'""",
            (user_id,),
        ).fetchone()["c"]
        return {
            "total": total,
            "completed": completed,
            "cancelled": cancelled,
            "failed": failed,
            "weight": weight,
            "rate": (completed / total) if total else 0,
        }

    def get_admin_overview(self):
        return {
            "users": self.conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"],
            "pickups": self.conn.execute("SELECT COUNT(*) c FROM pickup_request").fetchone()["c"],
            "recycling_logs": self.conn.execute("SELECT COUNT(*) c FROM recycling_log").fetchone()["c"],
            "notifications": self.conn.execute("SELECT COUNT(*) c FROM notification").fetchone()["c"],
        }

    def list_users(self):
        return self.conn.execute("SELECT u.user_login_id,u.name,u.role,u.total_points,u.is_active,COALESCE(z.name,'') zone_name FROM users u LEFT JOIN zone z ON z.zone_id=u.zone_id ORDER BY u.user_login_id").fetchall()

    def add_user(self, login_id: str, name: str, password: str, role: str, zone_id: int | None):
        self.conn.execute("INSERT INTO users(user_login_id,user_id,name,password_hash,role,zone_id) VALUES(?,?,?,?,?,?)", (login_id, login_id, name, hash_password(password), role, zone_id))
        self.conn.commit()

    def update_user(self, login_id: str, name: str, role: str, zone_id: int | None, password: str = "", active: int = 1):
        cols = ["name=?", "role=?", "zone_id=?", "is_active=?"]
        vals = [name, role, zone_id, active]
        if password:
            cols.append("password_hash=?")
            vals.append(hash_password(password))
        vals.append(login_id)
        self.conn.execute(f"UPDATE users SET {','.join(cols)} WHERE user_login_id=?", vals)
        self.conn.commit()

    def list_zones(self):
        return self.conn.execute("SELECT zone_id,name,is_active FROM zone ORDER BY zone_id").fetchall()

    def create_zone(self, name: str):
        self.conn.execute("INSERT INTO zone(name) VALUES(?)", (name,))
        self.conn.commit()

    def update_zone(self, zone_id: int, name: str, active: int = 1):
        self.conn.execute("UPDATE zone SET name=?,is_active=? WHERE zone_id=?", (name, active, zone_id))
        self.conn.commit()

    def send_notification_by_zone(self, zone_id: int, title: str, message: str):
        users = self.conn.execute("SELECT user_login_id FROM users WHERE zone_id=? AND is_active=1", (zone_id,)).fetchall()
        with self.transaction():
            for user in users:
                self.add_notification(user["user_login_id"], "SYSTEM", title, message)

    def close(self):
        self.conn.close()
