from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import TypeVar

from .errors import ClientError

T = TypeVar("T")


QUOTA_PATIENCE = 4  # a per-minute quota (429) needs seconds, not milliseconds: wait four times as long and try one more time


def with_retry[T](fn: Callable[[], T], *, attempts: int = 3, base: float = 1.0) -> T:
    """Retry retryable ClientErrors with jittered exponential backoff; quota errors (429) wait longer and get one more try."""
    last: Exception | None = None
    i = 0
    left = attempts
    while left > 0:
        try:
            return fn()
        except ClientError as e:
            last = e
            quota = getattr(e, "status", None) == 429
            if quota and left == attempts and i == 0:
                left += 1  # one extra attempt, once
            left -= 1
            if not e.retryable or left == 0:
                raise
            time.sleep(base * (2**i) * (QUOTA_PATIENCE if quota else 1) + random.random() * 0.25)
            i += 1
    raise last  # pragma: no cover
