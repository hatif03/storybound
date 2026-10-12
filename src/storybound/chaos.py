"""Failure injection for resilience drills. Off unless STORYBOUND_CHAOS is set **and** STORYBOUND_EXPERIMENT names the drill; never set in the product.

STORYBOUND_CHAOS="target:kind:param:probability,..." for example
    gemini:stall:100:0.2      20% of Gemini calls first wait 100 s (the 87 s Vertex stall, made worse)
    gemini:error:503:0.4      40% of Gemini calls fail with a 503
    k2:error:503:1            the K2 judge is down
    gateway:error:503:1       the hackathon gateway is down
    image:error:429:0.8       80% of picture calls hit the quota

Targets: gemini, k2, gateway, image, tts. Every injected failure is a real ClientError with the real retry rules, so the agent's own recovery
(retry, hedge, fall back, degrade) is what is being tested. Drills are tagged in the ledger (`chaos`) and in neatlogs (`STORYBOUND_TAGS=chaos`).
"""

from __future__ import annotations

import os
import random
import time

from .clients.errors import ClientError

_RETRYABLE = {408, 429, 499, 500, 502, 503, 504}


def enabled() -> bool:
    """A stray STORYBOUND_CHAOS in a product environment does nothing: a drill must also name itself (STORYBOUND_EXPERIMENT), as run_experiments.py does."""
    return bool(os.environ.get("STORYBOUND_CHAOS")) and bool(os.environ.get("STORYBOUND_EXPERIMENT"))


def rules() -> list[tuple[str, str, float, float]]:
    out: list[tuple[str, str, float, float]] = []
    if not enabled():
        return out
    for part in os.environ.get("STORYBOUND_CHAOS", "").split(","):
        bits = part.strip().split(":")
        if len(bits) == 4:
            try:
                out.append((bits[0], bits[1], float(bits[2]), float(bits[3])))
            except ValueError:
                continue
    return out


def active() -> str:
    return os.environ.get("STORYBOUND_CHAOS", "") if enabled() else ""


def maybe(target: str) -> None:
    """Called at the top of a client call: may sleep (a stall) or raise (an outage)."""
    for tgt, kind, param, p in rules():
        if tgt != target or random.random() >= p:
            continue
        if kind == "stall":
            time.sleep(param)
        elif kind == "error":
            status = int(param)
            raise ClientError(f"chaos: injected {status} on {target}", retryable=status in _RETRYABLE, status=status)
