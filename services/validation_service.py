"""Validation helpers for login, registration and pickup scheduling."""
import re
from datetime import datetime, timedelta

USER_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{4,19}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PASSWORD_UPPER_RE = re.compile(r"[A-Z]")
PASSWORD_LOWER_RE = re.compile(r"[a-z]")
PASSWORD_DIGIT_RE = re.compile(r"\d")
PASSWORD_SPECIAL_RE = re.compile(r"[^A-Za-z0-9]")


def require(value: str, label: str) -> str:
    text = (value or "").strip()
    if not text:
        raise ValueError(f"{label} is required.")
    return text


def validate_user_id(user_id: str) -> str:
    uid = (user_id or "").strip()
    if not USER_ID_RE.fullmatch(uid):
        raise ValueError("User ID must be 5-20 chars, start with a letter, and include only letters, digits, underscore.")
    return uid


def validate_password(password: str, user_id: str = "") -> str:
    pwd = require(password, "Password")
    if not (8 <= len(pwd) <= 64):
        raise ValueError("Password must be 8-64 characters.")
    if not PASSWORD_UPPER_RE.search(pwd):
        raise ValueError("Password must include uppercase letter.")
    if not PASSWORD_LOWER_RE.search(pwd):
        raise ValueError("Password must include lowercase letter.")
    if not PASSWORD_DIGIT_RE.search(pwd):
        raise ValueError("Password must include digit.")
    if not PASSWORD_SPECIAL_RE.search(pwd):
        raise ValueError("Password must include special character.")
    if user_id and user_id.lower() in pwd.lower():
        raise ValueError("Password must not contain user ID.")
    return pwd


def validate_login(user_id: str, password: str) -> tuple[str, str]:
    return validate_user_id(user_id), require(password, "Password")


def validate_registration_step1(user_id: str, password: str, confirm_password: str) -> tuple[str, str]:
    uid = validate_user_id(user_id)
    pwd = validate_password(password, uid)
    if pwd != (confirm_password or ""):
        raise ValueError("Passwords do not match.")
    return uid, pwd


def validate_pickup_datetime(date_text: str, time_text: str) -> datetime:
    dt = datetime.strptime(f"{date_text} {time_text}", "%Y-%m-%d %H:%M")
    if dt < datetime.now() + timedelta(minutes=30):
        raise ValueError("Pickup must be at least 30 minutes in the future.")
    if not (8 <= dt.hour <= 17 or (dt.hour == 18 and dt.minute == 0)):
        raise ValueError("Pickup time must be between 08:00 and 18:00.")
    if dt.minute not in (0, 30):
        raise ValueError("Pickup time must use 30-minute increments.")
    return dt


def validate_filling_info(data: dict) -> dict:
    cleaned = {
        "full_name": require(data.get("full_name", ""), "Full Name"),
        "id_no": require(data.get("id_no", ""), "Identification Card No. / Passport No."),
        "telephone": require(data.get("telephone", ""), "Telephone No."),
        "email": require(data.get("email", ""), "Email"),
        "zone": require(data.get("zone", ""), "Residential Zone"),
        "address": (data.get("address", "") or "").strip(),
    }
    if not EMAIL_RE.match(cleaned["email"].lower()):
        raise ValueError("Email format is invalid.")
    cleaned["email"] = cleaned["email"].lower()
    return cleaned
