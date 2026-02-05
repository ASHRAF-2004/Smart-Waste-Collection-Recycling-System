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
                locked_until TEXT
            );

            CREATE TABLE IF NOT EXISTS pickup_request (
                pickup_id INTEGER PRIMARY KEY AUTOINCREMENT,
                resident_id TEXT NOT NULL REFERENCES users(user_id),
                zone TEXT NOT NULL,
                requested_datetime TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
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

        self._safe_add_column("users", "role", "TEXT NOT NULL DEFAULT 'Resident'")
        self._safe_add_column("users", "address", "TEXT")
        self._safe_add_column("users", "total_points", "INTEGER NOT NULL DEFAULT 0")
        self._safe_add_column("users", "failed_attempts", "INTEGER NOT NULL DEFAULT 0")
        self._safe_add_column("users", "locked_until", "TEXT")
        self._safe_add_column("recycling_log", "points_awarded", "INTEGER NOT NULL DEFAULT 0")
        self._safe_add_column("pickup_request", "assigned_collector_id", "TEXT")
        self._safe_add_column("notification", "source_type", "TEXT NOT NULL DEFAULT 'SYSTEM'")

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
            ("admin@city.gov", hash_password("Admin#123"), "MunicipalAdmin", "City Admin", "admin@city.gov", "Zone A"),
        )
        self.conn.execute(
            """
            INSERT OR IGNORE INTO users(user_id,password_hash,role,full_name,email,zone)
            VALUES(?,?,?,?,?,?)
            """,
            ("2001", hash_password("Collector#123"), "WasteCollector", "Collector One", "collector1@waste.local", "Zone A"),
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
                SET full_name=?, id_no=?, telephone=?, email=?, zone=?, address=?, role=?
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
                "SELECT user_id,password_hash,failed_attempts,locked_until FROM users WHERE user_id=? OR lower(email)=lower(?)",
                (user_id, user_id),
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

    def unread_count(self, user_id: str) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) AS c FROM notification WHERE user_id=? AND read_at IS NULL",
            (user_id,),
        ).fetchone()
        return row["c"]

    def mark_notifications_read(self, user_id: str):
        self.conn.execute("UPDATE notification SET read_at=CURRENT_TIMESTAMP WHERE user_id=? AND read_at IS NULL", (user_id,))
        self.conn.commit()

    def admin_zone_crud(self, action: str, zone_name: str, old_name: str | None = None):
        if action == "add":
            self.conn.execute("INSERT INTO zone(zone_name) VALUES(?)", (zone_name,))
        elif action == "delete":
            self.conn.execute("DELETE FROM zone WHERE zone_name=?", (zone_name,))
        elif action == "edit" and old_name:
            self.conn.execute("UPDATE zone SET zone_name=? WHERE zone_name=?", (zone_name, old_name))
        self.conn.commit()

    def get_admin_stats(self) -> dict[str, Any]:
        waste = self.conn.execute(
            "SELECT zone, category, SUM(weight_kg) AS total FROM recycling_log rl JOIN users u ON u.user_id=rl.resident_id GROUP BY zone, category"
        ).fetchall()
        participation = self.conn.execute(
            "SELECT substr(logged_at,1,7) AS month, COUNT(DISTINCT resident_id) AS participants FROM recycling_log GROUP BY month ORDER BY month"
        ).fetchall()
        avg_pickup_time = self.conn.execute(
            """
            SELECT AVG((julianday(psu.timestamp)-julianday(pr.requested_datetime))*24) AS avg_hours
            FROM pickup_request pr JOIN pickup_status_update psu ON psu.pickup_id=pr.pickup_id
            WHERE psu.new_status IN ('COMPLETED','FAILED')
            """
        ).fetchone()["avg_hours"]
        return {"waste": waste, "participation": participation, "avg_pickup_hours": round(avg_pickup_time or 0, 2)}

    def get_collector_requests(self, collector_id: str):
        return self.conn.execute(
            "SELECT * FROM pickup_request WHERE assigned_collector_id=? ORDER BY requested_datetime DESC",
            (collector_id,),
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

    def list_pickup_requests(self):
        return self.conn.execute("SELECT * FROM pickup_request ORDER BY requested_datetime DESC").fetchall()

    def assign_pickup(self, pickup_id: int, collector_id: str):
        self.conn.execute("UPDATE pickup_request SET assigned_collector_id=? WHERE pickup_id=?", (collector_id, pickup_id))
        self.conn.commit()

    def add_notification(self, user_id: str, title: str, message: str, source_type: str = "SYSTEM"):
        self.conn.execute(
            "INSERT INTO notification(user_id,title,message,source_type) VALUES(?,?,?,?)",
            (user_id, title, message, source_type),
        )
        self.conn.commit()

    def list_users_by_role(self, role: str):
        return self.conn.execute("SELECT * FROM users WHERE role=?", (role,)).fetchall()

    def close(self):
        self.conn.close()
