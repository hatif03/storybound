"""Shared agent plumbing: a traced JSON call to the writer model, and a seeded RNG."""

from __future__ import annotations

import hashlib
import random

from .. import tracing
from ..clients import gateway, gemini
from ..clients.usage import Result
from ..config import get_settings


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

    chosen = model or get_settings().models.route(name)
    if chosen and gateway.is_gateway(chosen) and not gateway.configured():
        chosen = model  # no gateway key here (a test, or a machine without .env): use the default model

    @tracing.span(kind="AGENT", name=name)
    def _call() -> Result:
        if chosen and gateway.is_gateway(chosen):
            return gateway.generate_json(user, model=chosen, system=system, images=images, temperature=temperature, max_tokens=max_tokens)
        return gemini.generate_json(
            user, system=system, images=images, model=chosen, temperature=temperature, max_tokens=max_tokens
        )

    return _call()


def rng(seed: str, *parts: object) -> random.Random:
    h = hashlib.sha256("|".join([seed, *map(str, parts)]).encode()).digest()
    return random.Random(int.from_bytes(h[:8], "big"))
