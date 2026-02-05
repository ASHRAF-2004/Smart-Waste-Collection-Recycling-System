"""SQLite access layer for the prototype user journey."""
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
            logger.exception("Failed to initialize DB at %s", path)
            raise ValueError("Database is not available. Please try again later.") from exc

    def _init_schema(self):
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS zone (
                zone_id INTEGER PRIMARY KEY AUTOINCREMENT,
                zone_name TEXT UNIQUE NOT NULL
            );

            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'Resident' CHECK(role IN ('Resident','WasteCollector','MunicipalAdmin')),
                full_name TEXT,
                id_no TEXT,
                telephone TEXT,
                email TEXT UNIQUE,
                zone TEXT,
                address TEXT,
                total_points INTEGER NOT NULL DEFAULT 0,
                failed_attempts INTEGER NOT NULL DEFAULT 0,
                locked_until TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS pickup_request (
                pickup_id INTEGER PRIMARY KEY AUTOINCREMENT,
                resident_id TEXT NOT NULL REFERENCES users(user_id),
                zone TEXT NOT NULL,
                requested_datetime TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                scheduled_datetime TEXT,
                status TEXT NOT NULL DEFAULT 'PENDING' CHECK(status IN ('PENDING','COMPLETED','FAILED')),
                assigned_collector_id TEXT REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS pickup_status_update (
                status_update_id INTEGER PRIMARY KEY AUTOINCREMENT,
                pickup_id INTEGER NOT NULL REFERENCES pickup_request(pickup_id),
                updated_by_collector_id TEXT NOT NULL REFERENCES users(user_id),
                new_status TEXT NOT NULL CHECK(new_status IN ('PENDING','COMPLETED','FAILED')),
                timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                comment TEXT,
                evidence_image TEXT
            );

            CREATE TABLE IF NOT EXISTS recycling_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                resident_id TEXT NOT NULL REFERENCES users(user_id),
                category TEXT NOT NULL,
                weight_kg REAL NOT NULL,
                points_awarded INTEGER NOT NULL DEFAULT 0,
                logged_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                waste_image TEXT
            );

            CREATE TABLE IF NOT EXISTS reward_transactions (
                reward_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL REFERENCES users(user_id),
                source_log_id INTEGER REFERENCES recycling_log(log_id),
                points INTEGER NOT NULL,
                reason TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS notification (
                notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL REFERENCES users(user_id),
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                source_type TEXT NOT NULL DEFAULT 'SYSTEM' CHECK(source_type IN ('SYSTEM','ADMIN')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                read_at TEXT
            );
            """
        )

        self._safe_add_column("users", "created_at", "TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP")
        self._safe_add_column("users", "updated_at", "TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP")
        self._safe_add_column("pickup_request", "scheduled_datetime", "TEXT")
        self.conn.commit()

    def _safe_add_column(self, table: str, column: str, ddl: str):
        cols = [row["name"] for row in self.conn.execute(f"PRAGMA table_info({table})").fetchall()]
        if column not in cols:
            self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")

    def _seed_data(self):
        for zone_name in ("Zone A", "Zone B", "Zone C", "Zone D"):
            self.conn.execute("INSERT OR IGNORE INTO zone(zone_name) VALUES(?)", (zone_name,))

        self.conn.execute(
            """
            INSERT OR IGNORE INTO users(user_id,password_hash,role,full_name,email,zone)
            VALUES(?,?,?,?,?,?)
            """,
            ("admin01", hash_password("Admin#123"), "MunicipalAdmin", "City Admin", "admin@city.gov", "Zone A"),
        )
        self.conn.execute(
            """
            INSERT OR IGNORE INTO users(user_id,password_hash,role,full_name,email,zone)
            VALUES(?,?,?,?,?,?)
            """,
            ("collect01", hash_password("Collector#123"), "WasteCollector", "Collector One", "collector1@waste.local", "Zone A"),
        )
        resident_count = self.conn.execute("SELECT COUNT(*) AS c FROM users WHERE role='Resident'").fetchone()["c"]
        if resident_count == 0:
            self.conn.execute(
                """
                INSERT INTO users(user_id,password_hash,role,full_name,id_no,telephone,email,zone,address,total_points)
                VALUES(?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    "res1001",
                    hash_password("Resident#123"),
                    "Resident",
                    "Resident Sample",
                    "RES10001",
                    "0123456789",
                    "resident@example.com",
                    "Zone A",
                    "Jalan Contoh 1",
                    20,
                ),
            )

        pickup_count = self.conn.execute("SELECT COUNT(*) AS c FROM pickup_request").fetchone()["c"]
        if pickup_count == 0:
            self.conn.execute(
                """
                INSERT INTO pickup_request(resident_id,zone,requested_datetime,scheduled_datetime,status,assigned_collector_id)
                VALUES(?,?,?,?,?,?)
                """,
                ("res1001", "Zone A", "2026-01-10 10:00:00", "2026-01-11 09:00:00", "PENDING", "collect01"),
            )
        self.conn.commit()

    def _is_duplicate(self, user_id: str, email: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM users WHERE user_id=? OR lower(email)=lower(?)",
            (user_id, email),
        ).fetchone()
        return bool(row)

    def create_basic_user(self, user_id: str, password: str):
        try:
            self.conn.execute(
                "INSERT INTO users(user_id, password_hash) VALUES(?, ?)",
                (user_id, hash_password(password)),
            )
            self.conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError("error_duplicate_user") from exc

    def complete_profile(self, data: dict):
        try:
            if self._is_duplicate(data["user_id"], data["email"]):
                existing = self.conn.execute("SELECT user_id FROM users WHERE user_id=?", (data["user_id"],)).fetchone()
                if not existing:
                    raise ValueError("error_duplicate_user")

            cursor = self.conn.execute(
                """
                UPDATE users
                SET full_name=?, id_no=?, telephone=?, email=?, zone=?, address=?, role=?, updated_at=CURRENT_TIMESTAMP
                WHERE user_id=?
                """,
                (
                    data["full_name"],
                    data["id_no"],
                    data["telephone"],
                    data["email"],
                    data["zone"],
                    data.get("address", ""),
                    data["role"],
                    data["user_id"],
                ),
            )
            if cursor.rowcount == 0:
                raise ValueError("Registration session expired. Please start registration again.")
            self.conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError("error_duplicate_user") from exc

    def verify_credentials(self, user_id: str, password: str) -> tuple[bool, str | None]:
        try:
            user = self.conn.execute(
                "SELECT user_id,password_hash,failed_attempts,locked_until FROM users WHERE user_id=?",
                (user_id,),
            ).fetchone()
            if not user:
                return False, "invalid"

            lock_status = self.conn.execute(
                "SELECT datetime('now') < datetime(?) AS locked FROM users WHERE user_id=?",
                (user["locked_until"], user["user_id"]),
            ).fetchone()["locked"] if user["locked_until"] else 0
            if lock_status:
                return False, "locked"

            if verify_password(password, user["password_hash"]):
                self.conn.execute("UPDATE users SET failed_attempts=0, locked_until=NULL WHERE user_id=?", (user["user_id"],))
                self.conn.commit()
                return True, user["user_id"]

            attempts = user["failed_attempts"] + 1
            if attempts >= 5:
                self.conn.execute(
                    "UPDATE users SET failed_attempts=?, locked_until=datetime('now', '+10 minutes') WHERE user_id=?",
                    (attempts, user["user_id"]),
                )
            else:
                self.conn.execute("UPDATE users SET failed_attempts=? WHERE user_id=?", (attempts, user["user_id"]))
            self.conn.commit()
            return False, f"attempts_left:{max(0, 5 - attempts)}"
        except sqlite3.Error:
            logger.exception("Credential verification failed for user_id=%s", user_id)
            raise ValueError("Unable to verify credentials right now.")

    def get_user(self, user_id: str):
        return self.conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()

    def list_zones(self):
        return self.conn.execute("SELECT zone_name FROM zone ORDER BY zone_name").fetchall()

    def create_zone(self, zone_name: str):
        self.conn.execute("INSERT INTO zone(zone_name) VALUES(?)", (zone_name.strip(),))
        self.conn.commit()

    def update_zone(self, old_name: str, new_name: str):
        self.conn.execute("UPDATE zone SET zone_name=? WHERE zone_name=?", (new_name.strip(), old_name.strip()))
        self.conn.execute("UPDATE users SET zone=? WHERE zone=?", (new_name.strip(), old_name.strip()))
        self.conn.execute("UPDATE pickup_request SET zone=? WHERE zone=?", (new_name.strip(), old_name.strip()))
        self.conn.commit()

    def delete_zone(self, zone_name: str):
        self.conn.execute("UPDATE users SET zone='' WHERE zone=?", (zone_name.strip(),))
        self.conn.execute("UPDATE pickup_request SET zone='' WHERE zone=?", (zone_name.strip(),))
        self.conn.execute("DELETE FROM zone WHERE zone_name=?", (zone_name.strip(),))
        self.conn.commit()

    def list_users(self, sort_by: str = "full_name"):
        sort_cols = {"full_name": "full_name", "role": "role", "zone": "zone"}
        order_col = sort_cols.get(sort_by, "full_name")
        return self.conn.execute(
            f"""
            SELECT user_id,full_name,role,zone,telephone,email,total_points
            FROM users
            ORDER BY {order_col} COLLATE NOCASE ASC, user_id ASC
            """
        ).fetchall()

    def add_user(self, payload: dict):
        self.conn.execute(
            """
            INSERT INTO users(user_id,password_hash,role,full_name,id_no,telephone,email,zone,address)
            VALUES(?,?,?,?,?,?,?,?,?)
            """,
            (
                payload["user_id"],
                hash_password(payload["password"]),
                payload["role"],
                payload.get("full_name", ""),
                payload.get("id_no", ""),
                payload.get("telephone", ""),
                payload.get("email", "").lower(),
                payload.get("zone", ""),
                payload.get("address", ""),
            ),
        )
        self.conn.commit()

    def update_user(self, user_id: str, updates: dict):
        if not updates:
            return
        columns = []
        values = []
        for key, value in updates.items():
            if key == "password":
                columns.append("password_hash=?")
                values.append(hash_password(value))
            elif key in {"full_name", "role", "zone", "telephone", "email", "address", "id_no"}:
                columns.append(f"{key}=?")
                values.append(value.lower() if key == "email" else value)
        if not columns:
            return
        columns.append("updated_at=CURRENT_TIMESTAMP")
        values.append(user_id)
        self.conn.execute(f"UPDATE users SET {', '.join(columns)} WHERE user_id=?", values)
        self.conn.commit()

    def delete_user(self, user_id: str):
        self.conn.execute("DELETE FROM notification WHERE user_id=?", (user_id,))
        self.conn.execute("DELETE FROM reward_transactions WHERE user_id=?", (user_id,))
        self.conn.execute("DELETE FROM pickup_status_update WHERE updated_by_collector_id=?", (user_id,))
        self.conn.execute("UPDATE pickup_request SET assigned_collector_id=NULL WHERE assigned_collector_id=?", (user_id,))
        self.conn.execute("DELETE FROM pickup_request WHERE resident_id=?", (user_id,))
        self.conn.execute("DELETE FROM recycling_log WHERE resident_id=?", (user_id,))
        self.conn.execute("DELETE FROM users WHERE user_id=?", (user_id,))
        self.conn.commit()

    def create_recycling_log(self, resident_id: str, category: str, weight_kg: float) -> int:
        multiplier = {"plastic": 5, "paper": 3, "glass": 4, "metal": 6}.get(category.lower(), 2)
        points = int(weight_kg * multiplier)
        cur = self.conn.execute(
            "INSERT INTO recycling_log(resident_id,category,weight_kg,points_awarded) VALUES(?,?,?,?)",
            (resident_id, category, weight_kg, points),
        )
        self.conn.execute(
            "INSERT INTO reward_transactions(user_id,source_log_id,points,reason) VALUES(?,?,?,?)",
            (resident_id, cur.lastrowid, points, f"{category} recycling"),
        )
        self.conn.execute("UPDATE users SET total_points=total_points+? WHERE user_id=?", (points, resident_id))
        self.conn.commit()
        return points

    def get_zone_leaderboard(self):
        return self.conn.execute(
            """
            SELECT zone, full_name, user_id, total_points
            FROM users
            WHERE role='Resident'
            ORDER BY zone ASC, total_points DESC
            """
        ).fetchall()

    def get_notifications(self, user_id: str):
        return self.conn.execute(
            "SELECT * FROM notification WHERE user_id=? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()

    def get_admin_notifications(self):
        return self.conn.execute(
            """
            SELECT n.notification_id,n.user_id,u.full_name,n.title,n.message,n.created_at,n.source_type
            FROM notification n LEFT JOIN users u ON u.user_id=n.user_id
            ORDER BY n.created_at DESC
            """
        ).fetchall()

    def unread_count(self, user_id: str) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) AS c FROM notification WHERE user_id=? AND read_at IS NULL",
            (user_id,),
        ).fetchone()
        return row["c"]

    def mark_notifications_read(self, user_id: str):
        self.conn.execute("UPDATE notification SET read_at=CURRENT_TIMESTAMP WHERE user_id=? AND read_at IS NULL", (user_id,))
        self.conn.commit()

    def add_notification(self, user_id: str, title: str, message: str, source_type: str = "SYSTEM"):
        self.conn.execute(
            "INSERT INTO notification(user_id,title,message,source_type) VALUES(?,?,?,?)",
            (user_id, title, message, source_type),
        )
        self.conn.commit()

    def get_admin_stats(self) -> dict[str, Any]:
        users = self.conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        pickups = self.conn.execute("SELECT COUNT(*) AS c FROM pickup_request").fetchone()["c"]
        zones = self.conn.execute("SELECT COUNT(*) AS c FROM zone").fetchone()["c"]
        notes = self.conn.execute("SELECT COUNT(*) AS c FROM notification").fetchone()["c"]
        return {"users": users, "pickups": pickups, "zones": zones, "notifications": notes}

    def get_collector_requests(self, collector_id: str, zone_filter: str = "", status_filter: str = "", sort_by: str = "date"):
        clauses = ["pr.assigned_collector_id=?"]
        params: list[Any] = [collector_id]
        if zone_filter:
            clauses.append("pr.zone=?")
            params.append(zone_filter)
        if status_filter:
            clauses.append("pr.status=?")
            params.append(status_filter)
        order_clause = "pr.requested_datetime DESC" if sort_by == "date" else "pr.zone ASC, pr.requested_datetime DESC"
        return self.conn.execute(
            f"""
            SELECT pr.pickup_id,pr.resident_id,u.full_name AS resident_name,pr.zone,pr.requested_datetime,
                   pr.scheduled_datetime,pr.status,pr.assigned_collector_id
            FROM pickup_request pr
            LEFT JOIN users u ON u.user_id=pr.resident_id
            WHERE {' AND '.join(clauses)}
            ORDER BY {order_clause}
            """,
            params,
        ).fetchall()

    def update_pickup_status(self, collector_id: str, pickup_id: int, new_status: str, comment: str = "", evidence_image: str = ""):
        self.conn.execute("UPDATE pickup_request SET status=? WHERE pickup_id=?", (new_status, pickup_id))
        self.conn.execute(
            """
            INSERT INTO pickup_status_update(pickup_id,updated_by_collector_id,new_status,comment,evidence_image)
            VALUES(?,?,?,?,?)
            """,
            (pickup_id, collector_id, new_status, comment, evidence_image),
        )
        self.conn.commit()

    def collector_metrics(self, collector_id: str):
        completed = self.conn.execute(
            "SELECT COUNT(*) AS c FROM pickup_request WHERE assigned_collector_id=? AND status='COMPLETED'",
            (collector_id,),
        ).fetchone()["c"]
        points = completed * 10
        avg_hours = self.conn.execute(
            """
            SELECT AVG((julianday(psu.timestamp)-julianday(pr.requested_datetime))*24) AS avg_hours
            FROM pickup_request pr
            JOIN pickup_status_update psu ON psu.pickup_id=pr.pickup_id
            WHERE pr.assigned_collector_id=? AND psu.new_status IN ('COMPLETED','FAILED')
            """,
            (collector_id,),
        ).fetchone()["avg_hours"]
        return {"completed": completed, "points": points, "efficiency_hours": round(avg_hours or 0, 2)}

    def list_pickup_requests(self):
        return self.conn.execute("SELECT * FROM pickup_request ORDER BY requested_datetime DESC").fetchall()

    def assign_pickup(self, pickup_id: int, collector_id: str):
        self.conn.execute("UPDATE pickup_request SET assigned_collector_id=? WHERE pickup_id=?", (collector_id, pickup_id))
        self.conn.commit()

    def list_users_by_role(self, role: str):
        return self.conn.execute("SELECT * FROM users WHERE role=?", (role,)).fetchall()

    def close(self):
        self.conn.close()
