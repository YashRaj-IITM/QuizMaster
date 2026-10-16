import re
from datetime import date, datetime, timezone

from flask import jsonify, request
from flask_security import auth_required, roles_required

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DURATION_RE = re.compile(r"^([0-9]{1,2}):([0-5][0-9])$")


class ValidationError(Exception):
    """Raised for bad client input; converted to a 400 JSON response."""


def error(message, status=400):
    # "error" is what the Vue views read; "message" matches the other projects
    return jsonify({"success": False, "error": message, "message": message}), status


def json_body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object")
    return data


def token_roles(*roles):
    """Require a valid access token AND one of the given roles."""

    def decorator(fn):
        return auth_required("token")(roles_required(*roles)(fn))

    return decorator


def text(value, label, min_len=0, max_len=255, required=False):
    value = value.strip() if isinstance(value, str) else ""
    if required and not value:
        raise ValidationError(f"{label} is required")
    if value and len(value) < min_len:
        raise ValidationError(f"{label} must be at least {min_len} characters")
    if len(value) > max_len:
        raise ValidationError(f"{label} must be at most {max_len} characters")
    return value


def integer(value, label, lo=None, hi=None, required=True):
    if value is None or value == "":
        if required:
            raise ValidationError(f"{label} is required")
        return None
    if isinstance(value, bool):
        raise ValidationError(f"{label} must be a whole number")
    try:
        value = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{label} must be a whole number")
    if (lo is not None and value < lo) or (hi is not None and value > hi):
        raise ValidationError(f"{label} must be between {lo} and {hi}")
    return value


def parse_date(value, label="Date", required=True):
    """Parse YYYY-MM-DD (or an ISO date-time) into a naive datetime."""
    if value is None or value == "":
        if required:
            raise ValidationError(f"{label} is required")
        return None
    if not isinstance(value, str):
        raise ValidationError(f"{label} must be a date in YYYY-MM-DD format")
    try:
        dt = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        raise ValidationError(f"{label} must be a date in YYYY-MM-DD format")
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def parse_dob(value):
    dt = parse_date(value, "Date of birth", required=False)
    if dt is None:
        return None
    if dt.date() >= date.today():
        raise ValidationError("Date of birth must be in the past")
    return dt.date()


def duration(value):
    """Validate an 'HH:MM' quiz duration (00:01 .. 05:00)."""
    if value is None or value == "":
        return None
    match = DURATION_RE.match(value.strip()) if isinstance(value, str) else None
    if not match:
        raise ValidationError("Duration must be in HH:MM format, e.g. 00:30")
    minutes = int(match.group(1)) * 60 + int(match.group(2))
    if not 1 <= minutes <= 300:
        raise ValidationError("Duration must be between 00:01 and 05:00")
    return value.strip().zfill(5)
