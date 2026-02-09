"""Validate and normalize X/Twitter post URLs."""

import re

_TWITTER_URL_PATTERN = re.compile(
    r"^https?://(www\.)?(twitter\.com|x\.com)/[A-Za-z0-9_]{1,15}/status/\d+",
    re.IGNORECASE,
)


def validate_url(text: str) -> str | None:
    """Validate an X/Twitter post URL.

    Returns the cleaned URL if valid, or None if invalid.
    Strips query parameters and fragments.
    """
    text = text.strip()
    text = text.split("?")[0].split("#")[0]

    if _TWITTER_URL_PATTERN.match(text):
        return text

    return None
