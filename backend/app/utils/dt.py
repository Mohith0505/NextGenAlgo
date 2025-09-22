from __future__ import annotations

from datetime import datetime, timezone

__all__ = ["utcnow"]


def utcnow() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)
