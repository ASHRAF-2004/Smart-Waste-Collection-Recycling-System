"""SQLite access layer for the prototype user journey."""
import hashlib
import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)


class SQLiteService:
    def __init__(self, path: str = "db/prototype.db"):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        try:
            self.conn = sqlite3.connect(path)
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA foreign_keys = ON")
            self._init_schema()
        except sqlite3.Error as exc:
            logger.exception("Failed to initialize DB at %s", path)
            raise ValueError("Database is not available. Please try again later.") from exc

    def _init_schema(self):
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                id_no TEXT,
                telephone TEXT,
                email TEXT,
                zone TEXT
            )
            """
        )
        cols = [row["name"] for row in self.conn.execute("PRAGMA table_info(users)").fetchall()]
        self.user_columns = set(cols)
        if "password" in self.user_columns and "password_hash" not in self.user_columns:
            self.conn.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
            self.conn.execute("UPDATE users SET password_hash = password WHERE password_hash IS NULL")
        if "password_hash" not in self.user_columns and "password" not in self.user_columns:
            self.conn.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
        self.conn.commit()
        cols = [row["name"] for row in self.conn.execute("PRAGMA table_info(users)").fetchall()]
        self.user_columns = set(cols)

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def verify_credentials(self, user_id: str, password: str) -> bool:
        try:
            select_cols = ["password_hash"]
            if "password" in self.user_columns:
                select_cols.append("password")
            row = self.conn.execute(
                f"SELECT {', '.join(select_cols)} FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            if not row:
                return False
            supplied_hash = self._hash_password(password)
            stored_hash = row["password_hash"] if "password_hash" in row.keys() else None
            legacy_password = row["password"] if "password" in row.keys() else None
            if stored_hash and stored_hash == supplied_hash:
                return True
            if legacy_password and legacy_password == password:
                self.conn.execute(
                    "UPDATE users SET password_hash = ? WHERE user_id = ?",
                    (supplied_hash, user_id),
                )
                self.conn.commit()
                return True
            return False
        except sqlite3.Error:
            logger.exception("Credential verification failed for user_id=%s", user_id)
            raise ValueError("Unable to verify credentials right now.")

    def create_basic_user(self, user_id: str, password: str):
        try:
            self.conn.execute(
                "INSERT INTO users(user_id, password_hash) VALUES(?, ?)",
                (user_id, self._hash_password(password)),
            )
            self.conn.commit()
        except sqlite3.IntegrityError as exc:
            logger.warning("Duplicate user_id registration: %s", user_id)
            raise ValueError("This User ID is already registered. Please choose another one.") from exc
        except sqlite3.Error as exc:
            logger.exception("Failed to create basic user user_id=%s", user_id)
            raise ValueError("Unable to create user account at this time.") from exc

    def complete_profile(self, data: dict):
        try:
            cursor = self.conn.execute(
                """
                UPDATE users
                SET full_name=?, id_no=?, telephone=?, email=?, zone=?
                WHERE user_id=?
                """,
                (
                    data["full_name"],
                    data["id_no"],
                    data["telephone"],
                    data["email"],
                    data["zone"],
                    data["user_id"],
                ),
            )
            if cursor.rowcount == 0:
                raise ValueError("Registration session expired. Please start registration again.")
            self.conn.commit()
        except sqlite3.IntegrityError as exc:
            logger.exception("Integrity error completing profile user_id=%s", data.get("user_id"))
            raise ValueError("Unable to save profile due to related data constraints.") from exc
        except sqlite3.Error as exc:
            logger.exception("Failed to complete profile user_id=%s", data.get("user_id"))
            raise ValueError("Unable to save profile details right now.") from exc
