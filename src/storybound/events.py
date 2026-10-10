"""A tiny thread-safe event log: the pipeline appends, server-sent-event readers replay from any index."""

from __future__ import annotations

import threading
import time
from typing import Any


class EventLog:
    def __init__(self) -> None:
        self._events: list[dict[str, Any]] = []
        self._cv = threading.Condition()
        self._t0 = time.time()
        self.closed = False

    def emit(self, type_: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        with self._cv:
            ev = {"id": len(self._events), "type": type_, "t": round(time.time() - self._t0, 2), "data": data or {}}
            self._events.append(ev)
            self._cv.notify_all()
            return ev

    def close(self) -> None:
        with self._cv:
            self.closed = True
            self._cv.notify_all()

    def since(self, index: int, timeout: float = 15.0) -> tuple[list[dict[str, Any]], bool]:
        """Events from `index` on. Waits up to `timeout` for news. Returns (events, finished)."""
        with self._cv:
            if index >= len(self._events) and not self.closed:
                self._cv.wait(timeout)
            return self._events[index:], self.closed and index >= len(self._events)

    def all(self) -> list[dict[str, Any]]:
        with self._cv:
            return list(self._events)
