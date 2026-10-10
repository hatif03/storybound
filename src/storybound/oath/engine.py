"""The oath engine: deterministic verifiers first, a sampled independent judge second, one verdict object out.

Policy (docs/DESIGN.md section 3.3):
- deterministic fails -> that is the verdict; the judge is not consulted.
- deterministic passes (or none) -> the judge runs when seeded sampling says so; the stricter verdict wins.
- a judge that errors or fails the quote check: safety commitments fail closed (verification_error), quality
  commitments fail open as a flagged warning, so a story is never presented as checked when it was not.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from .. import tracing
from ..config import get_settings
from ..models import Commitment, Evidence, Oath, Page, Verdict
from . import catalog
from . import deterministic as d
from .judge import JudgeOut, judge_batch, judge_image

RANK = {"skipped": 0, "pass": 1, "warning": 2, "verification_error": 3, "violation": 4, "critical": 5}
Gate = Literal["accept", "repair", "critical"]


def sample_draw(seed: str, commitment: str, scope: str, attempt: int) -> float:
    """Deterministic uniform number in [0,1) so sampling is reproducible and recorded."""
    h = hashlib.sha256(f"{seed}|{commitment}|{scope}|{attempt}".encode()).digest()
    return int.from_bytes(h[:8], "big") / 2**64


def page_block(p: Page) -> str:
    lines = [f"PAGE {p.index}", f"Scenario: {p.scenario}", f"Question: {p.question}"]
    for c in p.choices:
        lines.append(f"Choice {c.id} [{'CORRECT' if c.is_correct else 'WRONG'}]: {c.text} | Feedback: {c.feedback}")
    lines.append(f"Image prompt: {p.image_prompt}")
    return "\n".join(lines)


def gate(v: Verdict, c: Commitment) -> Gate:
    """What the pipeline should do with one verdict."""
    if v.status in ("pass", "skipped", "warning"):
        return "accept"
    if v.status == "critical":
        return "critical"
    if v.status == "verification_error":
        return "critical" if c.klass == "safety" else "accept"
    return "repair"


@dataclass
class Engine:
    oath: Oath
    ctx: d.Ctx
    judge: Callable[[list[Commitment], str, dict], dict[str, JudgeOut]] = judge_batch
    judge_img: Callable[..., JudgeOut] = judge_image
    rates: dict[str, float] | None = None  # budget governor: may lower quality/image, never safety
    on_verdict: Callable[[Verdict], None] | None = None
    judge_enabled: bool = True  # False for the offline test mode; the receipt says so
    defer_judge_on_det_fail: bool = False  # the gated arm sets this; the observe-only arm judges every page

    # ---- plumbing -----------------------------------------------------------------------------------------------------

    def commitments(self, scope: str) -> list[Commitment]:
        return [c for c in self.oath.commitments if c.scope == scope]

    def get(self, cid: str) -> Commitment:
        return next(c for c in self.oath.commitments if c.id == cid)

    def rate(self, c: Commitment) -> float:
        s = get_settings().sampling
        if c.klass == "safety":
            return 1.0  # never lowered
        base = s.image if c.scope == "image" else 1.0 if c.id == "lesson_alignment" else s.quality
        if self.rates and c.scope == "image" and "image" in self.rates:
            return self.rates["image"]
        if self.rates and "quality" in self.rates and c.scope != "image":
            return self.rates["quality"]
        return base

    def _judge_context(self) -> dict:
        ctx: dict = {"age": self.ctx.age}
        if self.ctx.lesson:
            ctx["LESSON"] = self.ctx.lesson.concept
        if self.ctx.card:
            ctx["CHARACTER_CARD"] = self.ctx.card.model_dump()
        return ctx

    def _emit(self, v: Verdict, text: str) -> Verdict:
        v.trace_id = tracing.current_trace_id()
        with tracing.guardrail_span(v.commitment, scope=v.scope, input_text=text) as sp:
            tracing.record(sp, v.model_dump(mode="json"))
        if self.on_verdict:
            self.on_verdict(v)
        return v

    def _combine(self, c: Commitment, scope: str, attempt: int, det: d.Det | None, jo: JudgeOut | None,
                 sampled: bool, seed_tag: str | None) -> Verdict:  # fmt: skip
        v = Verdict(commitment=c.id, scope=scope, attempt=attempt, expected=c.plain, cover=c.cover,
                    sampled=sampled, sample_seed=seed_tag)  # fmt: skip
        if det:
            v.det_status = det.status
            v.actual = det.actual
            v.evidence = Evidence(scene=det.scene, matched=det.matched, quote=det.quote)
        if det and det.status != "pass":
            v.status = det.status  # type: ignore[assignment]
            v.verdict_by = "deterministic"
            return v
        if jo is None:
            v.status = "pass" if det else "skipped"
            v.verdict_by = "deterministic" if det else "none"
            return v
        v.judge_model, v.judge_status, v.score, v.reasoning = jo.model, jo.status, jo.score, jo.reasoning  # type: ignore[assignment]
        v.verdict_by = "both" if det else "judge"
        if jo.quote:
            v.evidence.quote = jo.quote
        if jo.status == "verification_error":
            v.actual = (v.actual + " | " if v.actual else "") + f"judge could not verify: {jo.error}"
            v.status = "verification_error" if c.klass == "safety" else "warning"
        else:
            v.status = jo.status  # type: ignore[assignment]
            if jo.reasoning:
                v.actual = jo.reasoning if not v.actual else f"{v.actual} | {jo.reasoning}"
        return v

    def _run(self, commitments: list[Commitment], label: str, subject, text: str, attempt: int, *,
             det_subject=None) -> list[Verdict]:  # fmt: skip
        """Verify every commitment of one scope over one subject."""
        dets: dict[str, d.Det | None] = {}
        for c in commitments:
            fn = catalog.DET.get(c.id)
            if fn is None:
                dets[c.id] = None
                continue
            try:
                dets[c.id] = fn(subject if det_subject is None else det_subject, self.ctx)
            except Exception as e:  # a crashing verifier is a verification error, never a pass
                dets[c.id] = d.Det("verification_error", f"verifier crashed: {type(e).__name__}: {e}"[:200])
        to_judge: list[Commitment] = []
        draws: dict[str, tuple[bool, str | None]] = {}
        # Deterministic first, at page level too: a page that already failed a cheap check will be repaired and judged
        # after the repair, so judging it now would only spend a slow call on text that is about to change. The last
        # attempt is always judged: a page never ships without its safety review.
        defer = (
            self.defer_judge_on_det_fail
            and attempt < get_settings().thresholds.max_repair_attempts
            and any(x is not None and x.status != "pass" for x in dets.values())
        )
        for c in commitments:
            if c.verifier == "deterministic" or defer:
                continue
            det = dets[c.id]
            if det is not None and det.status != "pass":
                continue
            rate = self.rate(c)
            u = sample_draw(self.ctx.seed, c.id, label, attempt)
            hit = self.judge_enabled and u < rate
            draws[c.id] = (hit, f"seed={self.ctx.seed} rate={rate:.2f} draw={u:.3f}")
            if hit:
                to_judge.append(c)
        outs = self.judge(to_judge, text, self._judge_context()) if to_judge else {}
        verdicts = []
        for c in commitments:
            hit, tag = draws.get(c.id, (False, None))
            v = self._combine(c, label, attempt, dets[c.id], outs.get(c.id), hit, tag)
            verdicts.append(self._emit(v, text))
        return verdicts

    # ---- public verification entry points -----------------------------------------------------------------------------

    def verify_scene(self, page: Page, attempt: int = 0) -> list[Verdict]:
        return self._run(self.commitments("scene"), f"scene {page.index}", page, page_block(page), attempt)

    def verify_story(self, pages: list[Page], attempt: int = 0) -> list[Verdict]:
        text = "\n\n".join(page_block(p) for p in pages)
        return self._run(self.commitments("story"), "story", pages, text, attempt)

    def verify_run(self, card, attempt: int = 0) -> list[Verdict]:
        text = json.dumps(card.model_dump(), ensure_ascii=False)
        return self._run(self.commitments("run"), "run", card, text, attempt)

    def verify_image_prompt(self, page: Page, attempt: int = 0) -> list[Verdict]:
        cs = [c for c in self.commitments("image") if c.id == "trait_in_image_prompt"]
        return self._run(cs, f"image {page.index}", page, page.image_prompt, attempt)

    def verify_image(self, page: Page, data: bytes | None, mime: str, attempt: int = 0) -> list[Verdict]:
        label = f"image {page.index}"
        out = []
        c = self.get("illustration_present")
        v = self._combine(c, label, attempt, d.illustration_present(data, self.ctx), None, False, None)
        out.append(self._emit(v, f"{len(data or b'')} bytes"))
        m = self.get("image_matches_card")
        if v.ok and data:
            rate = self.rate(m)
            u = sample_draw(self.ctx.seed, m.id, label, attempt)
            hit = self.judge_enabled and u < rate
            tag = f"seed={self.ctx.seed} rate={rate:.2f} draw={u:.3f}"
            jo = (
                self.judge_img(m, data, mime, json.dumps(self.ctx.card.model_dump())) if hit and self.ctx.card else None
            )
            vm = self._combine(m, label, attempt, None, jo, hit, tag)
        else:
            vm = self._combine(m, label, attempt, d.Det("pass"), None, False, None)
            vm.status, vm.verdict_by, vm.actual = "skipped", "none", "no image to compare"
        out.append(self._emit(vm, f"image {page.index}"))
        return out

    def verify_audio(self, page: Page, data: bytes | None, attempt: int = 0) -> list[Verdict]:
        label = f"audio {page.index}"
        c = self.get("narration_present")
        v = self._combine(
            c, label, attempt, d.narration_present(data, self.ctx, page.narration_text), None, False, None
        )
        return [self._emit(v, f"{len(data or b'')} bytes")]

    # ---- reporting ----------------------------------------------------------------------------------------------------

    def gate(self, v: Verdict) -> Gate:
        return gate(v, self.get(v.commitment))


OUTPUT_FIELDS = ["drawing", "character_card", "scenario", "question", "choices", "image_prompt", "image", "audio"]
TOOLS = {"safety_screen": "input_safe_visual", "illustrate": "illustration_present", "narrate": "narration_present"}


def coverage(oath: Oath) -> dict:
    """Which output fields and tools some commitment touches. Uncovered behaviour is where hardening looks first."""
    ids = {c.id for c in oath.commitments}
    fields = {f for c in oath.commitments for f in c.cover.split(",") if f}
    uncovered = [f for f in OUTPUT_FIELDS if f not in fields] + [t for t, cid in TOOLS.items() if cid not in ids]
    total = len(OUTPUT_FIELDS) + len(TOOLS)
    return {"pct": round(100 * (total - len(uncovered)) / total), "uncovered": uncovered}
