"""Authentication and registration service with RBAC checks."""
import sqlite3

from utils.errors import AuthorizationError, DatabaseError, ValidationError
from utils.security import hash_password, verify_password
from utils.validators import require_text


class AuthService:
    def __init__(self, user_dao):
        self.user_dao = user_dao

    def login(self, user_id_input: str, password: str):
        user_id_text = require_text(user_id_input, "User ID")
        password = require_text(password, "Password")
        if not user_id_text.isdigit():
            raise ValidationError("User ID must be numeric.")

        try:
            user = self.user_dao.get_by_id(int(user_id_text))
        except sqlite3.Error as exc:
            print(f"[DB] login failure: {exc}")
            raise DatabaseError("Database error during login.")

        if not user or not verify_password(password, user["password_hash"]):
            raise ValidationError("Wrong credentials.")
        return user

    def register_resident(self, name: str, password: str, zone_id=None):
        name = require_text(name, "Name")
        password = require_text(password, "Password")
        if len(password) < 4:
            raise ValidationError("Password must have at least 4 characters.")

        zone = int(zone_id) if zone_id not in (None, "") else None
        try:
            return self.user_dao.create_user(name, hash_password(password), "Resident", zone)
        except sqlite3.Error as exc:
            print(f"[DB] register failure: {exc}")
            raise DatabaseError("Could not register resident due to database issue.")

    def ensure_role(self, user, allowed_roles):
        if user["role"] not in allowed_roles:
            raise AuthorizationError("You are not authorized for this action.")
