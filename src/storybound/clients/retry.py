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


def hedged[T](fn: Callable[[], T], *, after: float) -> T:
    """Start `fn`; if it has not answered after `after` seconds start a second identical call and take whichever succeeds first.

    For a provider that sometimes stalls on one request until its timeout (the 87 s Vertex stall, HR-005/HR-011) while the same request
    sent again answers in seconds. Costs a second call only on a stall. The usage meter and the trace parent follow into both threads.
    `after <= 0` turns it off. If one call fails the other is still awaited; the last error is raised only when both fail.
    """
    import concurrent.futures as cf
    import contextvars

    if after <= 0:
        return fn()
    ex = cf.ThreadPoolExecutor(max_workers=2)
    try:
        first = ex.submit(contextvars.copy_context().run, fn)
        done, _ = cf.wait([first], timeout=after)
        if done:
            return first.result()
        second = ex.submit(contextvars.copy_context().run, fn)
        pending = {first, second}
        err: BaseException | None = None
        while pending:
            done, pending = cf.wait(pending, return_when=cf.FIRST_COMPLETED)
            for f in done:
                try:
                    return f.result()
                except BaseException as e:  # noqa: BLE001 - the other call may still succeed
                    err = e
        raise err  # type: ignore[misc]
    finally:
        ex.shutdown(wait=False)
