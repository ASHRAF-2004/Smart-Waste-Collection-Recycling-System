"""Validation helpers used by services."""
from utils.errors import ValidationError


def require_text(value: str, field_name: str) -> str:
    value = (value or "").strip()
    if not value:
        raise ValidationError(f"{field_name} is required.")
    return value


def require_positive_number(value, field_name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field_name} must be a number.")
    if number <= 0:
        raise ValidationError(f"{field_name} must be greater than 0.")
    return number
