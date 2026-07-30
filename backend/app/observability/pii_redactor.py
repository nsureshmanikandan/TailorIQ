"""PII redaction utilities for logs and traces."""
import re


EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_PATTERN = re.compile(
    r"\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"
)
ADDRESS_PATTERN = re.compile(
    r"\d{1,5}\s[\w\s]{1,30}(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)"
)


def redact_pii(text: str) -> str:
    """Remove PII patterns from text for safe logging.

    Redacts:
    - Email addresses
    - Phone numbers
    - Street addresses

    Args:
        text: Raw text that may contain PII.

    Returns:
        Text with PII patterns replaced by redaction markers.
    """
    result = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)
    result = PHONE_PATTERN.sub("[REDACTED_PHONE]", result)
    result = ADDRESS_PATTERN.sub("[REDACTED_ADDRESS]", result)
    return result
