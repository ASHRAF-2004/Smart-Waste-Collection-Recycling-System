"""SQLite access layer for the prototype user journey."""
import sqlite3
from pathlib import Path


class SQLiteService:
    def __init__(self, path: str = "db/prototype.db"):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                full_name TEXT,
                id_no TEXT,
                telephone TEXT,
                email TEXT,
                zone TEXT
            )
            """
        )
        self.conn.commit()

    def verify_credentials(self, user_id: str, password: str) -> bool:
        row = self.conn.execute(
            "SELECT user_id FROM users WHERE user_id = ? AND password = ?",
            (user_id, password),
        ).fetchone()
        return row is not None

    def create_basic_user(self, user_id: str, password: str):
        if self.conn.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,)).fetchone():
            raise ValueError("User ID already exists.")
        self.conn.execute(
            "INSERT INTO users(user_id, password) VALUES(?, ?)",
            (user_id, password),
        )
        self.conn.commit()

    def complete_profile(self, data: dict):
        self.conn.execute(
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
        self.conn.commit()
