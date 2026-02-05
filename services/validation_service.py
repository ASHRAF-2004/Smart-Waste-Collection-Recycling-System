"""Simple validation rules for academic prototype."""
import re


def require(value: str, label: str) -> str:
    text = (value or "").strip()
    if not text:
        raise ValueError(f"{label} is required.")
    return text


def validate_login(user_id: str, password: str) -> tuple[str, str]:
    return require(user_id, "User ID"), require(password, "Password")


def validate_registration_form(data: dict) -> dict:
    cleaned = {
        "user_id": require(data.get("user_id", ""), "User ID"),
        "password": require(data.get("password", ""), "Password"),
        "full_name": require(data.get("full_name", ""), "Full Name"),
        "id_no": require(data.get("id_no", ""), "Identification Card No. / Passport No."),
        "telephone": require(data.get("telephone", ""), "Telephone No."),
        "email": require(data.get("email", ""), "Email"),
        "zone": require(data.get("zone", ""), "Residential Zone"),
    }
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", cleaned["email"]):
        raise ValueError("Email format is invalid.")
    return cleaned
