"""neatlogs wiring. Everything here degrades to a no-op if tracing is unavailable: tracing never breaks a story."""

from __future__ import annotations

import contextlib
import json
import logging
from collections.abc import Iterator
from typing import Any

from .config import env

log = logging.getLogger("storybound.tracing")
_ready = False


def init() -> bool:
    """Initialise neatlogs once. Call before importing LLM libraries where possible."""
    global _ready
    if _ready:
        return True
    key = env("NEATLOGS_API_KEY")
    if not key:
        log.warning("NEATLOGS_API_KEY not set: tracing disabled")
        return False
    try:
        import neatlogs

        neatlogs.init(
            api_key=key,
            workflow_name=env("NEATLOGS_WORKFLOW", "create-storybook"),
            capture_logs=True,
        )
        _ready = True
    except Exception as e:  # pragma: no cover - depends on SDK/network
        log.warning("neatlogs init failed: %s", e)
    return _ready


def wrap(client: Any) -> Any:
    """Wrap a provider client so its calls become LLM spans (tokens, latency, cost)."""
    if not init():
        return client
    try:
        import neatlogs

        return neatlogs.wrap(client)
    except Exception as e:  # pragma: no cover
        log.warning("neatlogs.wrap failed: %s", e)
        return client


def span(kind: str = "TOOL", name: str | None = None, **kw: Any):
    """Decorator form of @neatlogs.span that is a no-op when tracing is off."""

    def deco(fn):
        if not init():
            return fn
        import neatlogs

        return neatlogs.span(kind=kind, name=name or fn.__name__, **kw)(fn)

    return deco


class _NullSpan:
    def set_attribute(self, *_a, **_k) -> None: ...


@contextlib.contextmanager
def guardrail_span(commitment: str, *, scope: str, input_text: str = "") -> Iterator[Any]:
    """One GUARDRAIL span per verdict. Set attributes through `record`."""
    if not init():
        yield _NullSpan()
        return
    import neatlogs

    with neatlogs.trace(f"verify:{commitment}", kind="GUARDRAIL") as s:
        s.set_attribute("neatlogs.guardrail.input", input_text[:4000])
        s.set_attribute("neatlogs.eval.commitment", commitment)
        s.set_attribute("neatlogs.eval.scope", scope)
        yield s


def record(span_obj: Any, verdict: dict) -> None:
    """Write a verdict (a plain dict) onto a guardrail span."""
    try:
        passed = verdict.get("status") in ("pass", "warning", "skipped")
        span_obj.set_attribute("neatlogs.guardrail.passed", passed)
        span_obj.set_attribute("neatlogs.guardrail.output", json.dumps(verdict, default=str)[:8000])
        for k in ("status", "attempt", "verdict_by", "judge_model", "sampled"):
            if k in verdict and verdict[k] is not None:
                span_obj.set_attribute(f"neatlogs.eval.{k}", verdict[k])
    except Exception as e:  # pragma: no cover
        log.warning("record failed: %s", e)


def flush() -> None:
    if not _ready:
        return
    try:
        import neatlogs

        neatlogs.flush()
    except Exception:  # pragma: no cover
        pass
