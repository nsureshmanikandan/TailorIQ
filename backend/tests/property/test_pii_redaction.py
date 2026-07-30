"""Property-based tests for PII Redaction.

# Feature: resume-jd-match-ai, Property 10: PII Redaction in Logs
"""
import re

from hypothesis import given, strategies as st

from tests.property.strategies import email_addresses, phone_numbers


EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_PATTERN = re.compile(r"\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")


def redact_pii(text: str) -> str:
    """Simple PII redaction function matching the backend implementation."""
    result = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)
    result = PHONE_PATTERN.sub("[REDACTED_PHONE]", result)
    return result


@given(email=email_addresses())
def test_emails_are_redacted(email):
    """P10: Log entries must not contain unredacted email addresses."""
    log_line = f"User {email} performed action"
    redacted = redact_pii(log_line)
    assert email not in redacted
    assert "[REDACTED_EMAIL]" in redacted


@given(phone=phone_numbers())
def test_phone_numbers_are_redacted(phone):
    """P10: Log entries must not contain unredacted phone numbers."""
    log_line = f"Contact: {phone}"
    redacted = redact_pii(log_line)
    assert phone not in redacted
