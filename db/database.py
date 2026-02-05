"""SQLite database setup and connection."""
import sqlite3
from pathlib import Path

from utils.security import hash_password

DB_PATH = Path("smart_waste.db")


class Database:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_schema_and_seed(self):
        first_run = not self.db_path.exists()
        with self.connect() as conn:
            cur = conn.cursor()
            cur.executescript(
                """
                CREATE TABLE IF NOT EXISTS zone (
                    zone_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    zone_name TEXT NOT NULL UNIQUE
                );

                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('Resident','WasteCollector','MunicipalAdmin')),
                    zone_id INTEGER NULL REFERENCES zone(zone_id),
                    total_points INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS pickup_request (
                    pickup_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    resident_id INTEGER NOT NULL REFERENCES users(user_id),
                    zone_id INTEGER NOT NULL REFERENCES zone(zone_id),
                    requested_datetime TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('PENDING','COMPLETED','FAILED'))
                );

                CREATE TABLE IF NOT EXISTS pickup_status_update (
                    status_update_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pickup_id INTEGER NOT NULL REFERENCES pickup_request(pickup_id),
                    updated_by_collector_id INTEGER NOT NULL REFERENCES users(user_id),
                    new_status TEXT NOT NULL CHECK(new_status IN ('PENDING','COMPLETED','FAILED')),
                    timestamp TEXT NOT NULL,
                    comment TEXT NULL,
                    evidence_image TEXT NULL
                );

                CREATE TABLE IF NOT EXISTS recycling_log (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    resident_id INTEGER NOT NULL REFERENCES users(user_id),
                    category TEXT NOT NULL,
                    weight_kg REAL NOT NULL,
                    logged_at TEXT NOT NULL,
                    waste_image TEXT NULL
                );

                CREATE TABLE IF NOT EXISTS notification (
                    notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL REFERENCES users(user_id),
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    read_at TEXT NULL
                );
                """
            )
            conn.commit()
            self._seed(conn, first_run)

    def _seed(self, conn, first_run: bool):
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS c FROM zone")
        if cur.fetchone()["c"] == 0:
            cur.execute("INSERT INTO zone(zone_name) VALUES (?)", ("Zone A",))
            cur.execute("INSERT INTO zone(zone_name) VALUES (?)", ("Zone B",))

        cur.execute("SELECT zone_id FROM zone WHERE zone_name=?", ("Zone A",))
        zone_a = cur.fetchone()["zone_id"]

        cur.execute("SELECT COUNT(*) AS c FROM users WHERE role='MunicipalAdmin' AND name='Admin'")
        if cur.fetchone()["c"] == 0:
            cur.execute(
                "INSERT INTO users(name,password_hash,role,zone_id,total_points) VALUES (?,?,?,?,0)",
                ("Admin", hash_password("admin123"), "MunicipalAdmin", None),
            )

        cur.execute("SELECT COUNT(*) AS c FROM users WHERE role='WasteCollector' AND name='CollectorA'")
        if cur.fetchone()["c"] == 0:
            cur.execute(
                "INSERT INTO users(name,password_hash,role,zone_id,total_points) VALUES (?,?,?,?,0)",
                ("CollectorA", hash_password("collector123"), "WasteCollector", zone_a),
            )

        conn.commit()

        if first_run:
            print("=== Seeded accounts ===")
            print("Admin -> name: Admin | password: admin123 | role: MunicipalAdmin")
            print("Collector -> name: CollectorA | password: collector123 | role: WasteCollector")
            print("Use displayed user IDs from DB list after first login or admin user manager.")
