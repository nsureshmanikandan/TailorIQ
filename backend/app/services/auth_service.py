"""Authentication service for JWT token management and password operations.

Provides token creation/validation, password hashing, and complexity validation
using python-jose for JWT operations and bcrypt for password hashing.
"""

import re
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt

from app.config import Settings, get_settings


# Precompiled regex patterns for password complexity
_HAS_UPPER = re.compile(r"[A-Z]")
_HAS_LOWER = re.compile(r"[a-z]")
_HAS_DIGIT = re.compile(r"\d")
_HAS_SPECIAL = re.compile(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?~`]")


def create_access_token(user_id: str, email: str, settings: Settings | None = None) -> str:
    """Create a short-lived JWT access token.

    Args:
        user_id: The user's UUID as a string.
        email: The user's email address.
        settings: Application settings (uses default if not provided).

    Returns:
        Encoded JWT access token string.
    """
    if settings is None:
        settings = get_settings()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": user_id,
        "email": email,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY.get_secret_value(),
        algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token(user_id: str, settings: Settings | None = None) -> str:
    """Create a long-lived JWT refresh token.

    Args:
        user_id: The user's UUID as a string.
        settings: Application settings (uses default if not provided).

    Returns:
        Encoded JWT refresh token string.
    """
    if settings is None:
        settings = get_settings()

    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY.get_secret_value(),
        algorithm=settings.JWT_ALGORITHM,
    )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash.

    Args:
        plain_password: The plaintext password to verify.
        hashed_password: The stored bcrypt hash.

    Returns:
        True if the password matches the hash.
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt.

    Args:
        password: The plaintext password to hash.

    Returns:
        Bcrypt hash string.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def validate_password_complexity(password: str) -> bool:
    """Validate that a password meets complexity requirements.

    Requirements:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character

    Args:
        password: The password to validate.

    Returns:
        True if the password meets all complexity requirements.
    """
    if len(password) < 8:
        return False
    if not _HAS_UPPER.search(password):
        return False
    if not _HAS_LOWER.search(password):
        return False
    if not _HAS_DIGIT.search(password):
        return False
    if not _HAS_SPECIAL.search(password):
        return False
    return True
