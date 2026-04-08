"""Spam and abuse filtering with keyword blocklist and rate limiting."""

import time
import logging

logger = logging.getLogger(__name__)

BLOCKLIST = [
    "buy now", "click here", "free money", "earn cash", "bitcoin doubler",
    "crypto giveaway", "investment opportunity", "act now", "limited offer",
    "congratulations you won", "claim your prize", "make money fast",
    "work from home guaranteed", "nigerian prince",
]

# Rate limit: max messages per user within a time window
RATE_LIMIT_MAX = 10
RATE_LIMIT_WINDOW = 60  # seconds

_rate_tracker: dict[int, list[float]] = {}


def is_blocked(message_text: str) -> bool:
    """Check if message matches any blocklist keyword."""
    text_lower = message_text.lower()
    return any(keyword in text_lower for keyword in BLOCKLIST)


def is_rate_limited(user_id: int) -> bool:
    """Check if user has exceeded the rate limit."""
    now = time.time()
    timestamps = _rate_tracker.get(user_id, [])
    timestamps = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]
    _rate_tracker[user_id] = timestamps

    if len(timestamps) >= RATE_LIMIT_MAX:
        return True

    timestamps.append(now)
    _rate_tracker[user_id] = timestamps
    return False


def check_message(user_id: int, message_text: str) -> str | None:
    """Run all filters. Returns a rejection reason string, or None if passed."""
    if is_rate_limited(user_id):
        return "rate_limited"
    if is_blocked(message_text):
        return "blocked_keyword"
    return None
