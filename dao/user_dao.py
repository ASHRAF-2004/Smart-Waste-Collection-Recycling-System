import sqlite3


class UserDAO:
    def __init__(self, db):
        self.db = db

    def create_user(self, name, password_hash, role, zone_id=None):
        with self.db.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users(name,password_hash,role,zone_id,total_points) VALUES (?,?,?,?,0)",
                (name, password_hash, role, zone_id),
            )
            conn.commit()
            return cur.lastrowid

    def get_by_id(self, user_id):
        with self.db.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
            return cur.fetchone()

    def update_user(self, user_id, name=None, password_hash=None, role=None, zone_id=None):
        fields, params = [], []
        if name is not None:
            fields.append("name=?")
            params.append(name)
        if password_hash is not None:
            fields.append("password_hash=?")
            params.append(password_hash)
        if role is not None:
            fields.append("role=?")
            params.append(role)
        if zone_id is not None:
            fields.append("zone_id=?")
            params.append(zone_id)
        if not fields:
            return
        params.append(user_id)
        with self.db.connect() as conn:
            cur = conn.cursor()
            cur.execute(f"UPDATE users SET {', '.join(fields)} WHERE user_id=?", tuple(params))
            conn.commit()

    def list_users(self):
        with self.db.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT u.*, z.zone_name FROM users u LEFT JOIN zone z ON u.zone_id=z.zone_id ORDER BY u.user_id")
            return cur.fetchall()

    def add_points(self, conn: sqlite3.Connection, resident_id, points_added):
        cur = conn.cursor()
        cur.execute("UPDATE users SET total_points = total_points + ? WHERE user_id=?", (points_added, resident_id))
