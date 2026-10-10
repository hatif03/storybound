from __future__ import annotations

import contextlib
import threading
from contextvars import ContextVar
from dataclasses import dataclass, field


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    latency_s: float = 0.0
    model: str = ""
    calls: int = 1

    def __add__(self, o: Usage) -> Usage:
        return Usage(
            self.input_tokens + o.input_tokens,
            self.output_tokens + o.output_tokens,
            self.latency_s + o.latency_s,
            self.model or o.model,
            self.calls + o.calls,
        )


@dataclass
class Result:
    """What every client returns: parsed payload (or raw text/bytes) plus usage."""

    value: object
    usage: Usage = field(default_factory=Usage)
    raw_text: str = ""


class Meter:
    """Counts what one story run spent, across threads. Set with `metered()`; clients call `record`."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.by_model: dict[str, dict[str, float]] = {}
        self.images = 0
        self.tts = 0

    def add(self, u: Usage, kind: str = "llm") -> None:
        with self._lock:
            row = self.by_model.setdefault(u.model or kind, {"in": 0, "out": 0, "calls": 0, "seconds": 0.0})
            row["in"] += u.input_tokens
            row["out"] += u.output_tokens
            row["calls"] += max(u.calls, 1)
            row["seconds"] += u.latency_s
            if kind == "image":
                self.images += 1
            elif kind == "tts":
                self.tts += 1

    def totals(self) -> dict:
        with self._lock:
            t_in = int(sum(r["in"] for r in self.by_model.values()))
            t_out = int(sum(r["out"] for r in self.by_model.values()))
            return {"tokens_in": t_in, "tokens_out": t_out, "images": self.images, "tts": self.tts,
                    "calls": int(sum(r["calls"] for r in self.by_model.values())),
                    "by_model": {k: dict(v) for k, v in self.by_model.items()}}  # fmt: skip

    def cost_usd(self, prices) -> float:
        """Estimated cost. Labelled an estimate wherever it is shown; neatlogs holds the measured number."""
        with self._lock:
            usd = 0.0
            for model, r in self.by_model.items():
                if model.startswith("IFM/"):
                    usd += (r["in"] + r["out"]) / 1e6 * prices.k2_per_m
                elif "image" in model or "tts" in model:
                    continue
                else:
                    usd += r["in"] / 1e6 * prices.gemini_in_per_m + r["out"] / 1e6 * prices.gemini_out_per_m
            return round(usd + self.images * prices.image_each + self.tts * prices.tts_each, 5)


_current: ContextVar[Meter | None] = ContextVar("storybound_meter", default=None)


def record(u: Usage, kind: str = "llm") -> None:
    m = _current.get()
    if m is not None:
        m.add(u, kind)


@contextlib.contextmanager
def metered():
    m = Meter()
    tok = _current.set(m)
    try:
        yield m
    finally:
        _current.reset(tok)
