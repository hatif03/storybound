"""Shared agent plumbing: a traced JSON call to the writer model, and a seeded RNG."""

from __future__ import annotations

import hashlib
import random

from .. import tracing
from ..clients import gemini
from ..clients.usage import Result


def ask_json(
    name: str,
    system: str,
    user: str,
    *,
    images: list[tuple[bytes, str]] | None = None,
    model: str | None = None,
    temperature: float = 0.4,
    max_tokens: int = 2048,
) -> Result:
    """One model call returning parsed JSON, under an AGENT span named `name` (so the trace reads like the graph)."""

    @tracing.span(kind="AGENT", name=name)
    def _call() -> Result:
        return gemini.generate_json(
            user, system=system, images=images, model=model, temperature=temperature, max_tokens=max_tokens
        )

    return _call()


def rng(seed: str, *parts: object) -> random.Random:
    h = hashlib.sha256("|".join([seed, *map(str, parts)]).encode()).digest()
    return random.Random(int.from_bytes(h[:8], "big"))
