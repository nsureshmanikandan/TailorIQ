"""Unit tests for the auth service module."""

import sys

sys.path.insert(0, ".")

from jose import jwt

from app.config import get_settings
from app.services.auth_service import (
    create_access_token,
    create_refresh_token,
    hash_password,
    validate_password_complexity,
    verify_password,
)


class TestPasswordHashing:
    """Tests for password hashing and verification."""

    def test_hash_and_verify_correct_password(self):
        hashed = hash_password("SecurePass1!")
        assert verify_password("SecurePass1!", hashed) is True

    def test_hash_and_verify_incorrect_password(self):
        hashed = hash_password("SecurePass1!")
        assert verify_password("WrongPassword!", hashed) is False

    def test_hashes_are_unique(self):
        hash1 = hash_password("SamePassword1!")
        hash2 = hash_password("SamePassword1!")
        assert hash1 != hash2  # bcrypt uses different salts


class TestPasswordComplexity:
    """Tests for password complexity validation."""

    def test_valid_password(self):
        assert validate_password_complexity("GoodPass1!") is True

    def test_too_short(self):
        assert validate_password_complexity("Sh0rt!") is False

    def test_no_uppercase(self):
        assert validate_password_complexity("lowercase1!") is False

    def test_no_lowercase(self):
        assert validate_password_complexity("UPPERCASE1!") is False

    def test_no_digit(self):
        assert validate_password_complexity("NoDigits!!") is False

    def test_no_special_char(self):
        assert validate_password_complexity("NoSpecial1") is False

    def test_minimum_length_boundary(self):
        # Exactly 8 chars meeting all requirements
        assert validate_password_complexity("Abcde1!x") is True

    def test_seven_chars_fails(self):
        assert validate_password_complexity("Abcd1!x") is False


class TestTokenCreation:
    """Tests for JWT token creation."""

    def test_access_token_contains_expected_claims(self):
        settings = get_settings()
        token = create_access_token("user-123", "test@example.com")
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY.get_secret_value(),
            algorithms=[settings.JWT_ALGORITHM],
        )
        assert payload["sub"] == "user-123"
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_refresh_token_contains_expected_claims(self):
        settings = get_settings()
        token = create_refresh_token("user-456")
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY.get_secret_value(),
            algorithms=[settings.JWT_ALGORITHM],
        )
        assert payload["sub"] == "user-456"
        assert payload["type"] == "refresh"
        assert "exp" in payload
        assert "iat" in payload
        assert "email" not in payload

    def test_access_token_is_string(self):
        token = create_access_token("user-1", "u@e.com")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_refresh_token_is_string(self):
        token = create_refresh_token("user-1")
        assert isinstance(token, str)
        assert len(token) > 0
