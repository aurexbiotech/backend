import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any, Optional
from pwdlib import PasswordHash
from config import settings

# Initialize password hasher (uses Argon2id by default)
_password_hasher = PasswordHash.recommended()


def hash_password(plain_password: str) -> str:
    """Securely hashes a plaintext password using Argon2id."""
    return _password_hasher.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Securely verifies a plaintext password against a stored hash."""
    try:
        return _password_hasher.verify(plain_password, hashed_password)
    except Exception:
        return False


def normalize_role(role: Optional[str]) -> str:
    """Normalizes role strings and display names into standard internal keys.

    Examples:
        'Front Desk' -> 'front_desk'
        'Lab Assistant' -> 'laboratory'
        'lab' -> 'laboratory'
        'lab_technician' -> 'laboratory'
        'Pharmacy' -> 'pharmacy'
        'pharmacist' -> 'pharmacy'
        'Department' -> 'department'
    """
    if not role:
        return ""
    cleaned = role.strip().lower().replace(" ", "_").replace("-", "_")

    role_aliases = {
        # Laboratory variations
        "lab": "laboratory",
        "laboratory": "laboratory",
        "lab_assistant": "laboratory",
        "lab_technician": "laboratory",
        # Pharmacy variations
        "pharmacy": "pharmacy",
        "pharmacist": "pharmacy",
        # Front desk variations
        "front_desk": "front_desk",
        "frontdesk": "front_desk",
        # Department
        "department": "department",
        # Standard roles
        "patient": "patient",
        "doctor": "doctor",
        "nurse": "nurse",
        "insurance": "insurance",
        "administrator": "administrator",
        "admin": "administrator",
    }
    return role_aliases.get(cleaned, cleaned)


def roles_match(selected_role: str, user_role: str) -> bool:
    """Returns True if the selected role matches the user's role in the database."""
    return normalize_role(selected_role) == normalize_role(user_role)


def create_session_token(user_id: str, role: str) -> str:
    """Creates a cryptographically signed session token using HMAC-SHA256."""
    ttl_seconds = settings.SESSION_TTL_HOURS * 3600
    payload: dict[str, Any] = {
        "user_id": user_id,
        "role": role,
        "exp": int(time.time()) + ttl_seconds,
    }
    payload_json = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(payload_json).decode("utf-8").rstrip("=")

    signature = hmac.new(
        settings.APP_SECRET_KEY.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return f"{payload_b64}.{signature}"


def decode_session_token(token: str) -> Optional[dict[str, Any]]:
    """Validates the signature and expiration of a session token.

    Returns the decoded payload dict if valid, or None if invalid/expired.
    """
    if not token or "." not in token:
        return None

    try:
        payload_b64, signature = token.split(".", 1)

        expected_sig = hmac.new(
            settings.APP_SECRET_KEY.encode("utf-8"),
            payload_b64.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_sig):
            return None

        # Add back base64 padding if needed
        padding = "=" * (-len(payload_b64) % 4)
        raw_json = base64.urlsafe_b64decode(payload_b64 + padding).decode("utf-8")
        payload = json.loads(raw_json)

        # Check expiration
        if payload.get("exp", 0) < time.time():
            return None

        return payload
    except Exception:
        return None


def generate_csrf_token() -> str:
    """Generates a secure random 32-byte CSRF token as hex string."""
    return secrets.token_hex(32)
