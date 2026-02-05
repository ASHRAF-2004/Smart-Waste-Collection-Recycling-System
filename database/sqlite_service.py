"""SQLite data access layer for the Smart Waste Collection prototype."""
from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any

from utils.security import hash_password, verify_password

logger = logging.getLogger(__name__)


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
            self._seed_data()
        except sqlite3.Error as exc:
            logger.exception("Database initialization failed")
            raise ValueError("Database is not available. Please try again later.") from exc

    def _init_schema(self):
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS zone (
                zone_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                service_start_time TEXT,
                service_end_time TEXT
            );

            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
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

            CREATE TABLE IF NOT EXISTS collector_zone_assignment (
                collector_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                zone_id INTEGER NOT NULL REFERENCES zone(zone_id) ON DELETE CASCADE,
                PRIMARY KEY (collector_id, zone_id)
            );

            CREATE TABLE IF NOT EXISTS pickup_request (
                pickup_id INTEGER PRIMARY KEY AUTOINCREMENT,
                resident_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                zone_id INTEGER NOT NULL REFERENCES zone(zone_id),
                requested_datetime TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PENDING' CHECK(status IN ('PENDING','IN_PROGRESS','COMPLETED','FAILED')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS pickup_status_update (
                status_update_id INTEGER PRIMARY KEY AUTOINCREMENT,
                pickup_id INTEGER NOT NULL REFERENCES pickup_request(pickup_id) ON DELETE CASCADE,
                collector_id TEXT NOT NULL REFERENCES users(user_id),
                new_status TEXT NOT NULL CHECK(new_status IN ('PENDING','IN_PROGRESS','COMPLETED','FAILED')),
                timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                comment TEXT,
                evidence_image TEXT
            );

            CREATE TABLE IF NOT EXISTS recycling_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                resident_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                category TEXT NOT NULL,
                weight_kg REAL NOT NULL,
                waste_image TEXT,
                points_added INTEGER NOT NULL DEFAULT 0,
                logged_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS reward_transaction (
                reward_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                source_log_id INTEGER REFERENCES recycling_log(log_id) ON DELETE SET NULL,
                points INTEGER NOT NULL,
                reason TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS notification (
                notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                type TEXT NOT NULL CHECK(type IN ('PICKUP_REMINDER','RECYCLING_TIP','STATUS_UPDATE','SYSTEM')),
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                read_at TEXT
            );
            """
        )
        self.conn.commit()

    def _seed_data(self):
        for name in ("Zone A", "Zone B"):
            self.conn.execute("INSERT OR IGNORE INTO zone(name) VALUES(?)", (name,))

        zone_a = self.get_zone_id_by_name("Zone A")
        self.conn.execute(
            """
            INSERT OR IGNORE INTO users(user_id,name,password_hash,role,zone_id,email)
            VALUES(?,?,?,?,?,?)
            """,
            ("Admin001", "Municipal Admin", hash_password("Admin123A"), "MunicipalAdmin", zone_a, "admin@local.demo"),
        )
        self.conn.execute(
            """
            INSERT OR IGNORE INTO users(user_id,name,password_hash,role,zone_id,email)
            VALUES(?,?,?,?,?,?)
            """,
            ("Collect1", "Collector One", hash_password("Collect123A"), "WasteCollector", zone_a, "collector@local.demo"),
        )
        self.conn.execute(
            "INSERT OR IGNORE INTO collector_zone_assignment(collector_id,zone_id) VALUES(?,?)",
            ("Collect1", zone_a),
        )
        self.conn.commit()

    def get_zone_id_by_name(self, name: str) -> int | None:
        row = self.conn.execute("SELECT zone_id FROM zone WHERE name=?", (name,)).fetchone()
        return row["zone_id"] if row else None

    def create_basic_user(self, user_id: str, password: str):
        try:
            self.conn.execute(
                "INSERT INTO users(user_id,password_hash,role) VALUES(?,?,'Resident')",
                (user_id, hash_password(password)),
            )
            self.conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError("error_duplicate_user") from exc

    def complete_profile(self, data: dict):
        zone_id = self.get_zone_id_by_name(data["zone"])
        if not zone_id:
            raise ValueError("Selected zone is not available.")
        try:
            cur = self.conn.execute(
                """
                UPDATE users
                SET name=?, passport_no=?, phone=?, email=?, zone_id=?, address=?
                WHERE user_id=?
                """,
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
        except sqlite3.IntegrityError as exc:
            raise ValueError("error_duplicate_user") from exc

    def verify_credentials(self, user_id: str, password: str) -> tuple[bool, str | None]:
        user = self.conn.execute(
            "SELECT user_id,password_hash,failed_attempts,locked_until,is_active FROM users WHERE user_id=?",
            (user_id,),
        ).fetchone()
        if not user or user["is_active"] == 0:
            return False, "invalid"

        if user["locked_until"]:
            locked = self.conn.execute("SELECT datetime('now') < datetime(?) AS y", (user["locked_until"],)).fetchone()["y"]
            if locked:
                return False, "locked"

        if verify_password(password, user["password_hash"]):
            self.conn.execute("UPDATE users SET failed_attempts=0, locked_until=NULL WHERE user_id=?", (user_id,))
            self.conn.commit()
            return True, user_id

        attempts = user["failed_attempts"] + 1
        if attempts >= 5:
            self.conn.execute(
                "UPDATE users SET failed_attempts=?, locked_until=datetime('now','+10 minutes') WHERE user_id=?",
                (attempts, user_id),
            )
        else:
            self.conn.execute("UPDATE users SET failed_attempts=? WHERE user_id=?", (attempts, user_id))
        self.conn.commit()
        return False, f"attempts_left:{max(0, 5-attempts)}"

    def get_user(self, user_id: str):
        return self.conn.execute(
            """
            SELECT u.*, z.name AS zone_name
            FROM users u
            LEFT JOIN zone z ON z.zone_id=u.zone_id
            WHERE u.user_id=?
            """,
            (user_id,),
        ).fetchone()

    def list_zones(self):
        return self.conn.execute("SELECT * FROM zone ORDER BY name").fetchall()

    def create_zone(self, name: str):
        self.conn.execute("INSERT INTO zone(name) VALUES(?)", (name.strip(),))
        self.conn.commit()

    def update_zone(self, old_name: str, new_name: str):
        self.conn.execute("UPDATE zone SET name=? WHERE name=?", (new_name.strip(), old_name.strip()))
        self.conn.commit()

    def delete_zone(self, name: str):
        zone_id = self.get_zone_id_by_name(name)
        if not zone_id:
            return
        linked = self.conn.execute(
            "SELECT (SELECT COUNT(*) FROM users WHERE zone_id=?) + (SELECT COUNT(*) FROM pickup_request WHERE zone_id=?) AS c",
            (zone_id, zone_id),
        ).fetchone()["c"]
        if linked:
            raise ValueError("Zone is in use by users or pickups.")
        self.conn.execute("DELETE FROM zone WHERE zone_id=?", (zone_id,))
        self.conn.commit()

    def list_users(self, sort_by: str = "name"):
        col_map = {"name": "u.name", "role": "u.role", "zone": "z.name"}
        col = col_map.get(sort_by, "u.name")
        return self.conn.execute(
            f"""
            SELECT u.user_id,u.name,u.role,COALESCE(z.name,'' ) AS zone,u.phone,u.email,u.total_points,u.is_active
            FROM users u
            LEFT JOIN zone z ON z.zone_id=u.zone_id
            ORDER BY {col} COLLATE NOCASE, u.user_id
            """
        ).fetchall()

    def add_user(self, payload: dict):
        zone_id = self.get_zone_id_by_name(payload.get("zone", "")) if payload.get("zone") else None
        self.conn.execute(
            """
            INSERT INTO users(user_id,name,password_hash,role,zone_id,email,phone,passport_no,address)
            VALUES(?,?,?,?,?,?,?,?,?)
            """,
            (
                payload["user_id"],
                payload.get("full_name", ""),
                hash_password(payload["password"]),
                payload["role"],
                zone_id,
                payload.get("email", "").lower() or None,
                payload.get("telephone", ""),
                payload.get("id_no", ""),
                payload.get("address", ""),
            ),
        )
        if payload["role"] == "WasteCollector" and zone_id:
            self.conn.execute(
                "INSERT OR IGNORE INTO collector_zone_assignment(collector_id,zone_id) VALUES(?,?)",
                (payload["user_id"], zone_id),
            )
        self.conn.commit()

    def update_user(self, user_id: str, updates: dict):
        sets, vals = [], []
        mapping = {"full_name": "name", "role": "role", "telephone": "phone", "email": "email", "address": "address", "id_no": "passport_no", "is_active": "is_active"}
        for k, v in updates.items():
            if k == "password":
                sets.append("password_hash=?")
                vals.append(hash_password(v))
            elif k == "zone":
                sets.append("zone_id=?")
                vals.append(self.get_zone_id_by_name(v) if v else None)
            elif k in mapping:
                sets.append(f"{mapping[k]}=?")
                vals.append(v.lower() if k == "email" else v)
        if not sets:
            return
        vals.append(user_id)
        self.conn.execute(f"UPDATE users SET {', '.join(sets)} WHERE user_id=?", vals)
        self.conn.commit()

    def delete_user(self, user_id: str):
        self.conn.execute("DELETE FROM users WHERE user_id=?", (user_id,))
        self.conn.commit()

    def assign_collector_zone(self, collector_id: str, zone_name: str):
        zid = self.get_zone_id_by_name(zone_name)
        if not zid:
            raise ValueError("Zone not found")
        self.conn.execute("INSERT OR IGNORE INTO collector_zone_assignment(collector_id,zone_id) VALUES(?,?)", (collector_id, zid))
        self.conn.execute("UPDATE users SET zone_id=? WHERE user_id=?", (zid, collector_id))
        self.conn.commit()

    def create_pickup_request(self, resident_id: str, requested_datetime: str):
        user = self.get_user(resident_id)
        if not user or not user["zone_id"]:
            raise ValueError("Resident zone is not configured.")
        self.conn.execute(
            "INSERT INTO pickup_request(resident_id,zone_id,requested_datetime) VALUES(?,?,?)",
            (resident_id, user["zone_id"], requested_datetime),
        )
        self.conn.commit()

    def list_resident_pickups(self, resident_id: str):
        return self.conn.execute(
            """
            SELECT p.pickup_id,p.requested_datetime,p.status,p.created_at,z.name AS zone_name
            FROM pickup_request p JOIN zone z ON z.zone_id=p.zone_id
            WHERE p.resident_id=? ORDER BY p.requested_datetime DESC
            """,
            (resident_id,),
        ).fetchall()

    def get_pickup_updates(self, pickup_id: int):
        return self.conn.execute(
            "SELECT * FROM pickup_status_update WHERE pickup_id=? ORDER BY timestamp DESC",
            (pickup_id,),
        ).fetchall()

    def get_collector_requests(self, collector_id: str, status_filter: str = "", sort_by: str = "requested"):
        sort_sql = "p.requested_datetime ASC" if sort_by == "requested" else "p.created_at ASC"
        where = ""
        params: list[Any] = [collector_id]
        if status_filter:
            where = "AND p.status=?"
            params.append(status_filter)
        return self.conn.execute(
            f"""
            SELECT p.pickup_id,p.resident_id,COALESCE(u.name,p.resident_id) AS resident_name,z.name AS zone_name,
                   COALESCE(u.address,'') AS address,p.requested_datetime,p.created_at,p.status
            FROM pickup_request p
            JOIN collector_zone_assignment cza ON cza.zone_id=p.zone_id
            JOIN zone z ON z.zone_id=p.zone_id
            LEFT JOIN users u ON u.user_id=p.resident_id
            WHERE cza.collector_id=? {where}
            ORDER BY {sort_sql}
            """,
            params,
        ).fetchall()

    def update_pickup_status(self, collector_id: str, pickup_id: int, new_status: str, comment: str = "", evidence_image: str = ""):
        self.conn.execute("UPDATE pickup_request SET status=? WHERE pickup_id=?", (new_status, pickup_id))
        self.conn.execute(
            "INSERT INTO pickup_status_update(pickup_id,collector_id,new_status,comment,evidence_image) VALUES(?,?,?,?,?)",
            (pickup_id, collector_id, new_status, comment, evidence_image),
        )
        resident = self.conn.execute("SELECT resident_id FROM pickup_request WHERE pickup_id=?", (pickup_id,)).fetchone()
        if resident:
            self.add_notification(resident["resident_id"], "STATUS_UPDATE", "Pickup status update", f"Your pickup #{pickup_id} is {new_status}.")
        self.conn.commit()

    def create_recycling_log(self, resident_id: str, category: str, weight_kg: float, waste_image: str = "") -> int:
        points = int(weight_kg * 10)
        cur = self.conn.execute(
            "INSERT INTO recycling_log(resident_id,category,weight_kg,waste_image,points_added) VALUES(?,?,?,?,?)",
            (resident_id, category, weight_kg, waste_image, points),
        )
        self.conn.execute("INSERT INTO reward_transaction(user_id,source_log_id,points,reason) VALUES(?,?,?,?)", (resident_id, cur.lastrowid, points, f"{category} recycling"))
        self.conn.execute("UPDATE users SET total_points=total_points+? WHERE user_id=?", (points, resident_id))
        self.conn.commit()
        return points

    def list_recycling_logs(self, resident_id: str):
        return self.conn.execute(
            "SELECT * FROM recycling_log WHERE resident_id=? ORDER BY logged_at DESC",
            (resident_id,),
        ).fetchall()

    def add_notification(self, user_id: str, note_type: str, title: str, message: str):
        self.conn.execute(
            "INSERT INTO notification(user_id,type,title,message) VALUES(?,?,?,?)",
            (user_id, note_type, title, message),
        )
        self.conn.commit()

    def get_notifications(self, user_id: str):
        return self.conn.execute("SELECT * FROM notification WHERE user_id=? ORDER BY created_at DESC", (user_id,)).fetchall()

    def mark_notifications_read(self, user_id: str):
        self.conn.execute("UPDATE notification SET read_at=CURRENT_TIMESTAMP WHERE user_id=? AND read_at IS NULL", (user_id,))
        self.conn.commit()

    def unread_count(self, user_id: str) -> int:
        return self.conn.execute("SELECT COUNT(*) AS c FROM notification WHERE user_id=? AND read_at IS NULL", (user_id,)).fetchone()["c"]

    def get_admin_notifications(self):
        return self.conn.execute(
            "SELECT n.*,u.name FROM notification n LEFT JOIN users u ON u.user_id=n.user_id ORDER BY n.created_at DESC"
        ).fetchall()

    def get_admin_stats(self) -> dict[str, Any]:
        counts = {
            "users": self.conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"],
            "recycling_weight": self.conn.execute("SELECT COALESCE(SUM(weight_kg),0) AS c FROM recycling_log").fetchone()["c"],
        }
        status_rows = self.conn.execute("SELECT status,COUNT(*) AS c FROM pickup_request GROUP BY status").fetchall()
        for s in ("PENDING", "IN_PROGRESS", "COMPLETED", "FAILED"):
            counts[s] = 0
        for row in status_rows:
            counts[row["status"]] = row["c"]
        counts["pickups"] = sum(counts[s] for s in ("PENDING", "IN_PROGRESS", "COMPLETED", "FAILED"))
        return counts

    def get_top_recyclers(self, limit: int = 5):
        return self.conn.execute(
            "SELECT user_id,name,total_points FROM users WHERE role='Resident' ORDER BY total_points DESC LIMIT ?",
            (limit,),
        ).fetchall()

    def get_dashboard_metrics(self) -> dict[str, float]:
        pickups = self.conn.execute("SELECT COUNT(*) AS c FROM pickup_request").fetchone()["c"]
        completed = self.conn.execute("SELECT COUNT(*) AS c FROM pickup_request WHERE status='COMPLETED'").fetchone()["c"]
        weight = self.conn.execute("SELECT COALESCE(SUM(weight_kg),0) AS w FROM recycling_log").fetchone()["w"]
        avg_const = 3.5
        denom = weight + pickups * avg_const
        rate = (weight / denom * 100) if denom else 0
        return {"pickups": pickups, "completed": completed, "recycled_weight": weight, "recycling_rate": rate}

    def send_upcoming_pickup_reminders(self, resident_id: str):
        rows = self.conn.execute(
            """
            SELECT pickup_id,requested_datetime FROM pickup_request
            WHERE resident_id=? AND status='PENDING' AND
                  datetime(requested_datetime) BETWEEN datetime('now') AND datetime('now','+24 hours')
            """,
            (resident_id,),
        ).fetchall()
        for row in rows:
            self.add_notification(resident_id, "PICKUP_REMINDER", "Pickup Reminder", f"Pickup #{row['pickup_id']} is scheduled at {row['requested_datetime']}.")

    def close(self):
        self.conn.close()
