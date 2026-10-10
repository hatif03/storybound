from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import TypeVar

from .errors import ClientError

T = TypeVar("T")


def with_retry[T](fn: Callable[[], T], *, attempts: int = 3, base: float = 1.0) -> T:
    """Retry retryable ClientErrors with jittered exponential backoff."""
    last: Exception | None = None
    for i in range(attempts):
        try:
            return fn()
        except ClientError as e:
            last = e
            if not e.retryable or i == attempts - 1:
                raise
            time.sleep(base * (2**i) + random.random() * 0.25)
    raise last  # pragma: no cover
