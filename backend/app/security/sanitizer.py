"""Input sanitizer for prompt injection defense.

Strips known prompt injection patterns from user-provided text (resumes,
job descriptions) before passing to AI agents. Patterns are replaced with
[REDACTED] to maintain text structure while neutralizing injection attempts.
"""

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Known prompt injection patterns (case-insensitive)
_INJECTION_PATTERNS: list[tuple[str, str]] = [
    # Direct instruction override attempts
    (r"ignore\s+(all\s+)?previous\s+instructions?", "[REDACTED]"),
    (r"ignore\s+(all\s+)?above\s+instructions?", "[REDACTED]"),
    (r"disregard\s+(all\s+)?previous\s+instructions?", "[REDACTED]"),
    (r"disregard\s+(all\s+)?above\s+instructions?", "[REDACTED]"),
    (r"forget\s+everything(\s+above)?", "[REDACTED]"),
    (r"forget\s+(all\s+)?previous\s+(context|instructions?)", "[REDACTED]"),
    # System prompt impersonation
    (r"system\s*:\s*you\s+are", "[REDACTED]"),
    (r"system\s*:\s*act\s+as", "[REDACTED]"),
    (r"system\s*:\s*ignore", "[REDACTED]"),
    (r"\[system\]", "[REDACTED]"),
    (r"\[INST\]", "[REDACTED]"),
    (r"<<SYS>>", "[REDACTED]"),
    (r"<\|im_start\|>system", "[REDACTED]"),
    # Role manipulation
    (r"you\s+are\s+now\s+a", "[REDACTED]"),
    (r"pretend\s+you\s+are", "[REDACTED]"),
    (r"act\s+as\s+if\s+you\s+are", "[REDACTED]"),
    (r"from\s+now\s+on\s+you\s+are", "[REDACTED]"),
    (r"your\s+new\s+role\s+is", "[REDACTED]"),
    # Output manipulation
    (r"output\s+the\s+following\s+exactly", "[REDACTED]"),
    (r"repeat\s+after\s+me", "[REDACTED]"),
    (r"respond\s+with\s+only", "[REDACTED]"),
    (r"do\s+not\s+follow\s+your\s+instructions?", "[REDACTED]"),
    (r"override\s+(your\s+)?instructions?", "[REDACTED]"),
    # Data exfiltration attempts
    (r"reveal\s+your\s+(system\s+)?prompt", "[REDACTED]"),
    (r"show\s+me\s+your\s+(system\s+)?prompt", "[REDACTED]"),
    (r"what\s+are\s+your\s+instructions?", "[REDACTED]"),
    (r"print\s+your\s+system\s+message", "[REDACTED]"),
    # Delimiter injection
    (r"---\s*end\s+of\s+(system\s+)?prompt\s*---", "[REDACTED]"),
    (r"===\s*new\s+instructions?\s*===", "[REDACTED]"),
    # Encoded injection (base64 markers)
    (r"base64\s*decode\s*:", "[REDACTED]"),
    (r"eval\s*\(", "[REDACTED]"),
]

# Pre-compile patterns for performance
_COMPILED_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(pattern, re.IGNORECASE), replacement)
    for pattern, replacement in _INJECTION_PATTERNS
]


@dataclass
class SanitizationResult:
    """Result of input sanitization.

    Attributes:
        sanitized_text: The cleaned text with patterns replaced.
        original_text: The original input text.
        patterns_found: List of pattern descriptions that were matched.
        was_modified: Whether any patterns were found and replaced.
    """

    sanitized_text: str
    original_text: str
    patterns_found: list[str] = field(default_factory=list)
    was_modified: bool = False


def sanitize_input(text: str) -> SanitizationResult:
    """Sanitize user input by replacing known prompt injection patterns.

    Scans the input text for known prompt injection patterns and replaces
    matches with [REDACTED]. The original text is preserved in the result
    for audit logging.

    Args:
        text: Raw user input text (resume content, job description, etc.).

    Returns:
        SanitizationResult with sanitized text and metadata about replacements.
    """
    if not text:
        return SanitizationResult(
            sanitized_text="",
            original_text="",
            patterns_found=[],
            was_modified=False,
        )

    sanitized = text
    patterns_found: list[str] = []

    for compiled_pattern, replacement in _COMPILED_PATTERNS:
        matches = compiled_pattern.findall(sanitized)
        if matches:
            patterns_found.append(compiled_pattern.pattern)
            sanitized = compiled_pattern.sub(replacement, sanitized)

    was_modified = len(patterns_found) > 0

    if was_modified:
        logger.warning(
            "Input sanitizer detected %d injection pattern(s): %s",
            len(patterns_found),
            [p[:50] for p in patterns_found],
        )

    return SanitizationResult(
        sanitized_text=sanitized,
        original_text=text,
        patterns_found=patterns_found,
        was_modified=was_modified,
    )


def sanitize_batch(texts: list[str]) -> list[SanitizationResult]:
    """Sanitize multiple text inputs.

    Args:
        texts: List of raw text inputs to sanitize.

    Returns:
        List of SanitizationResult objects, one per input.
    """
    return [sanitize_input(text) for text in texts]


def is_suspicious(text: str) -> bool:
    """Quick check if text contains any known injection patterns.

    Lighter-weight than full sanitization — useful for pre-screening.

    Args:
        text: Text to check for injection patterns.

    Returns:
        True if any injection pattern is detected.
    """
    if not text:
        return False

    for compiled_pattern, _ in _COMPILED_PATTERNS:
        if compiled_pattern.search(text):
            return True
    return False
