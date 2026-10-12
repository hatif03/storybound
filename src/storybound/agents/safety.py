"""The safety screen: an independent vision pass over the drawing before any story exists.

Tier A (visual danger) refuses. Tier B (harmful, instruction-like or personal words written in the drawing, harmless
pixels) sanitises: the words are ignored and recorded. A drawing that is not usable asks for a redraw, which is not a
safety event. If the screen itself fails, the answer is refuse (fail closed).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .. import prompts, tracing
from ..clients.errors import ClientError
from ..media import Drawing
from ..models import Evidence, Verdict
from ..oath import deterministic as d
from ..safety_terms import harm_hits, instruction_hits
from .common import ask_json

SEVERE = {"weapon", "blood_or_gore", "violence", "sexual", "self_harm", "hate_symbol", "drugs"}
Action = Literal["proceed", "sanitise", "refuse", "ask_redraw"]
PLACEHOLDER = "[personal details]"


@dataclass
class SafetyResult:
    action: Action
    tier: Literal["none", "A", "B"]
    reason_code: str
    verdict: Verdict
    ignored_text: list[str] = field(default_factory=list)  # in memory only; PII is already a placeholder
    categories: list[str] = field(default_factory=list)
    description: str = ""
    tokens_in: int = 0
    tokens_out: int = 0


def _verdict(status: str, actual: str, matched: str | None = None) -> Verdict:
    return Verdict(
        commitment="input_safe_visual",
        scope="run",
        status=status,  # type: ignore[arg-type]
        verdict_by="judge",
        expected="The drawing is safe to turn into a story.",
        actual=actual,
        evidence=Evidence(matched=matched),
        cover="drawing",
    )


def _emit(v: Verdict) -> Verdict:
    v.trace_id = tracing.current_trace_id()
    with tracing.guardrail_span(v.commitment, scope="run", input_text="drawing") as sp:
        tracing.record(sp, v.model_dump(mode="json"))
    return v


def _is_harmful_text(s: str) -> bool:
    return bool(harm_hits(s) or instruction_hits(s) or d.find_pii(s) or s.strip() == PLACEHOLDER)


@tracing.span(kind="TOOL", name="safety_screen")
def screen(drawing: Drawing) -> SafetyResult:
    if drawing.too_small:
        return SafetyResult("ask_redraw", "none", "too_small", _emit(_verdict("skipped", "picture too small to read")))
    if drawing.blank:
        return SafetyResult("ask_redraw", "none", "blank", _emit(_verdict("skipped", "no drawing found on the page")))
    try:
        r = ask_json(
            "safety_screen.vision",
            prompts.SAFETY_SYSTEM,
            prompts.SAFETY_USER,
            images=[(drawing.data, drawing.mime)],
            temperature=0,
            max_tokens=700,
        )
        j = r.value
        if not isinstance(j, dict) or "visual_risk" not in j:
            raise ClientError("screen answer missing visual_risk")
    except Exception as e:  # fail closed: the screen could not say the drawing is safe
        # an outage (a service error that outlived its retries) is not the drawing's fault; a block or an unreadable answer is treated as a refusal
        outage = isinstance(e, ClientError) and e.retryable
        msg = f"safety screen unavailable ({type(e).__name__})"
        v = _emit(_verdict("verification_error", msg))
        return SafetyResult("refuse", "A", "screen_unavailable" if outage else "screen_inconclusive", v)

    cats = [str(c) for c in j.get("risk_categories", []) if isinstance(c, str)]
    risk = str(j.get("visual_risk", "")).lower()
    desc = str(j.get("description", ""))[:200]
    texts = [str(t).strip() for t in j.get("text_in_drawing", []) if str(t).strip()]
    if j.get("personal_info"):
        texts = [PLACEHOLDER if d.find_pii(t) else t for t in texts]
        if PLACEHOLDER not in texts:
            texts.append(PLACEHOLDER)
    common = dict(categories=cats, description=desc, tokens_in=r.usage.input_tokens, tokens_out=r.usage.output_tokens)

    severe = SEVERE & set(cats)
    if risk == "severe" or severe or harm_hits(desc):
        why = ", ".join(sorted(severe)) or risk or "unsafe description"
        v = _emit(_verdict("critical", f"unsafe drawing: {why}", matched=why))
        return SafetyResult("refuse", "A", "unsafe_image", v, **common)
    if not j.get("readable", True) or not j.get("has_character", True):
        return SafetyResult("ask_redraw", "none", "no_character", _emit(_verdict("skipped", "no hero found")), **common)
    v = _emit(_verdict("pass", "drawing is safe"))
    if any(_is_harmful_text(t) for t in texts):
        return SafetyResult("sanitise", "B", "drawing_text_ignored", v, ignored_text=texts, **common)
    return SafetyResult("proceed", "none", "ok", v, ignored_text=texts, **common)
