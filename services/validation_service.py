"""Validation helpers for login and registration flow."""
import re

USER_ID_RE = re.compile(r"^[A-Za-z0-9]{5,10}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PASSWORD_UPPER_RE = re.compile(r"[A-Z]")
PASSWORD_LOWER_RE = re.compile(r"[a-z]")
PASSWORD_DIGIT_RE = re.compile(r"\d")
PASSWORD_SYMBOL_RE = re.compile(r"[^A-Za-z0-9]")
NAME_RE = re.compile(r"^[A-Za-z ]+$")
ALNUM_RE = re.compile(r"^[A-Za-z0-9]+$")
PHONE_RE = re.compile(r"^\d{9,12}$")


def require(value: str, label: str) -> str:
    text = (value or "").strip()
    if not text:
        raise ValueError(f"{label} is required.")
    return text


def is_valid_user_identifier(user_id: str) -> bool:
    uid = (user_id or "").strip()
    return bool(USER_ID_RE.match(uid))


def validate_user_id(user_id: str) -> str:
    uid = (user_id or "").strip()
    if not is_valid_user_identifier(uid):
        raise ValueError("error_user_id")
    return uid


def validate_password(password: str, user_id: str = "") -> str:
    pwd = require(password, "Password")
    if (
        " " in pwd
        or len(pwd) < 8
        or not PASSWORD_UPPER_RE.search(pwd)
        or not PASSWORD_LOWER_RE.search(pwd)
        or not PASSWORD_DIGIT_RE.search(pwd)
        or not PASSWORD_SYMBOL_RE.search(pwd)
    ):
        raise ValueError("error_password_strength")
    if user_id and pwd == user_id:
        raise ValueError("error_password_strength")
    return pwd


def validate_login(user_id: str, password: str) -> tuple[str, str]:
    uid = validate_user_id(user_id)
    pwd = require(password, "Password")
    return uid, pwd


def validate_registration_step1(user_id: str, password: str, confirm_password: str) -> tuple[str, str]:
    uid = validate_user_id(user_id)
    pwd = validate_password(password, uid)
    if pwd != (confirm_password or ""):
        raise ValueError("error_password_match")
    return uid, pwd


def validate_filling_info(data: dict) -> dict:
    cleaned = {
        "full_name": require(data.get("full_name", ""), "Full Name"),
        "id_no": require(data.get("id_no", ""), "Identification Card No. / Passport No."),
        "telephone": require(data.get("telephone", ""), "Telephone No."),
        "email": require(data.get("email", ""), "Email"),
        "zone": require(data.get("zone", ""), "Residential Zone"),
        "address": (data.get("address", "") or "").strip(),
        "role": require(data.get("role", ""), "Role"),
    }

    if len(cleaned["full_name"]) < 3 or not NAME_RE.match(cleaned["full_name"]):
        raise ValueError("Full Name must be at least 3 characters and contain only letters/spaces.")
    if len(cleaned["id_no"]) < 6 or not ALNUM_RE.match(cleaned["id_no"]):
        raise ValueError("Passport / ID must be at least 6 characters and alphanumeric only.")
    if not PHONE_RE.match(cleaned["telephone"]):
        raise ValueError("Telephone No. must be numeric and 9-12 digits.")

    cleaned["email"] = cleaned["email"].lower()
    if not EMAIL_RE.match(cleaned["email"]):
        raise ValueError("Email format is invalid.")

    cleaned["id_no"] = cleaned["id_no"].upper()
    if cleaned["role"] not in ("Resident", "WasteCollector"):
        raise ValueError("Role is invalid.")
    return cleaned


def collect_filling_info_errors(data: dict) -> dict[str, str]:
    errors = {}
    name = (data.get("full_name") or "").strip()
    if not name:
        errors["full_name"] = "Full Name is required."
    elif len(name) < 3 or not NAME_RE.match(name):
        errors["full_name"] = "Only letters/spaces; min 3 chars."

    id_no = (data.get("id_no") or "").strip()
    if not id_no:
        errors["id_no"] = "Passport / ID is required."
    elif len(id_no) < 6 or not ALNUM_RE.match(id_no):
        errors["id_no"] = "Alphanumeric only; min 6 chars."

    phone = (data.get("telephone") or "").strip()
    if not phone:
        errors["telephone"] = "Telephone is required."
    elif not PHONE_RE.match(phone):
        errors["telephone"] = "Digits only; 9-12 length."

    email = (data.get("email") or "").strip().lower()
    if not email:
        errors["email"] = "Email is required."
    elif not EMAIL_RE.match(email):
        errors["email"] = "Enter a valid email address."

    zone = (data.get("zone") or "").strip()
    if not zone:
        errors["zone"] = "Please select a zone."

    role = (data.get("role") or "").strip()
    if role not in ("Resident", "WasteCollector"):
        errors["role"] = "Please select a valid role."

    return errors
