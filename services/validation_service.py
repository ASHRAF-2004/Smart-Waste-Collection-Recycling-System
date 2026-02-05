"""Validation helpers for login and registration flow."""
import re

USER_ID_RE = re.compile(r"^\d{3,10}$")
PASSWORD_UPPER_RE = re.compile(r"[A-Z]")
PASSWORD_LOWER_RE = re.compile(r"[a-z]")
PASSWORD_DIGIT_RE = re.compile(r"\d")
NAME_RE = re.compile(r"^[A-Za-z ]+$")
ALNUM_RE = re.compile(r"^[A-Za-z0-9]+$")
PHONE_RE = re.compile(r"^\d{9,12}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def require(value: str, label: str) -> str:
    text = (value or "").strip()
    if not text:
        raise ValueError(f"{label} is required.")
    return text


def validate_user_id(user_id: str) -> str:
    uid = (user_id or "").strip()
    if not USER_ID_RE.match(uid):
        raise ValueError("User ID must be numeric and 3-10 digits long.")
    return uid


def validate_password(password: str, user_id: str = "") -> str:
    pwd = require(password, "Password")
    if " " in pwd:
        raise ValueError("Password cannot contain spaces.")
    if len(pwd) < 8:
        raise ValueError("Password must be at least 8 characters.")
    if not PASSWORD_UPPER_RE.search(pwd):
        raise ValueError("Password must include at least 1 uppercase letter.")
    if not PASSWORD_LOWER_RE.search(pwd):
        raise ValueError("Password must include at least 1 lowercase letter.")
    if not PASSWORD_DIGIT_RE.search(pwd):
        raise ValueError("Password must include at least 1 digit.")
    if user_id and pwd == user_id:
        raise ValueError("Password cannot be the same as User ID.")
    return pwd


def validate_login(user_id: str, password: str) -> tuple[str, str]:
    uid = validate_user_id(user_id)
    pwd = require(password, "Password")
    return uid, pwd


def validate_registration_step1(user_id: str, password: str, confirm_password: str) -> tuple[str, str]:
    uid = validate_user_id(user_id)
    pwd = validate_password(password, uid)
    if pwd != (confirm_password or ""):
        raise ValueError("Confirm Password must match Password.")
    return uid, pwd


def validate_filling_info(data: dict) -> dict:
    cleaned = {
        "full_name": require(data.get("full_name", ""), "Full Name"),
        "id_no": require(data.get("id_no", ""), "Identification Card No. / Passport No."),
        "telephone": require(data.get("telephone", ""), "Telephone No."),
        "email": require(data.get("email", ""), "Email"),
        "zone": require(data.get("zone", ""), "Residential Zone"),
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
    return cleaned


def validate_registration_form(data: dict) -> dict:
    uid = validate_user_id(data.get("user_id", ""))
    pwd = validate_password(data.get("password", ""), uid)
    profile = validate_filling_info(data)
    return {"user_id": uid, "password": pwd, **profile}


def collect_filling_info_errors(data: dict) -> dict[str, str]:
    errors = {}
    try:
        validate_filling_info(data)
    except ValueError:
        pass

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

    return errors
