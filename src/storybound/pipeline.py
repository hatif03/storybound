"""The story run as a LangGraph state machine.

intake -> safety -> character -> oath -> plan -> [write -> verify -> (repair | regen | accept)]x8 -> story gate -> media -> receipt

Arm B1 gates and repairs inside the run. Arm B0 (observe-only) writes the story in one call and only evaluates it
afterwards; nothing is gated or repaired. Both arms share the safety screen, the character card and the oath, so the
only thing that differs is whether verification is allowed to change the outcome.
"""

from __future__ import annotations

import concurrent.futures as cf
import contextvars
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from . import ledger, lessons, prompts, tracing
from .agents import character, oath_author, planner, safety, writer
from .agents.common import rng
from .clients import images, tts
from .clients.errors import ClientError
from .clients.usage import Meter, metered
from .config import get_settings
from .events import EventLog
from .media import Drawing
from .models import CharacterCard, Oath, Page, Verdict
from .oath import catalog
from .oath import deterministic as d
from .oath.engine import Engine, coverage
from .textutil import norm_ws

CALM_REFUSAL = "This drawing isn't one I can turn into a story. Could we try a different picture together?"
CALM_REDRAW = "I couldn't quite see a hero in that picture. Could you draw one a little bigger and darker?"
CALM_STOP = "I couldn't make this story gentle enough, so I stopped. Could we try another picture?"


@dataclass
class RunConfig:
    lesson_id: str
    age: int = 6
    hero_name: str | None = None
    arm: str = "B1"
    seed: str = "1"
    media: bool = True
    run_dir: Path | None = None
    fixture: str | None = None
    ledger_name: str | None = None
    judge_enabled: bool = True


class S(TypedDict, total=False):
    halt: str | None  # None | refused | ask_redraw | stopped | error
    card: CharacterCard
    oath: Oath
    beats: list[dict]
    pages: list[Page]
    i: int
    pending: Page
    attempt: int
    regens: int
    slots: list[int]
    route: str
    vs: list[Verdict]
    notes: list[dict]


def _public_page(p: Page) -> dict:
    return p.model_dump()


@dataclass
class Run:
    cfg: RunConfig
    drawing: Drawing
    bus: EventLog
    meter: Meter = field(default_factory=Meter)
    verdicts: list[Verdict] = field(default_factory=list)
    repairs: list[dict] = field(default_factory=list)
    degradations: list[dict] = field(default_factory=list)
    shipped: list[dict] = field(default_factory=list)
    ignored: list[str] = field(default_factory=list)
    safety_result: safety.SafetyResult | None = None
    engine: Engine | None = None
    ctx: d.Ctx = field(default_factory=d.Ctx)
    story_id: str = ""
    trace_id: str = ""
    outcome: str = ""
    error: str = ""
    receipt: dict | None = None
    t0: float = 0.0
    media_paths: dict[str, str] = field(default_factory=dict)
    lock: threading.Lock = field(default_factory=threading.Lock)

    # ---- helpers ------------------------------------------------------------------------------------------------------

    def emit(self, type_: str, data: dict | None = None) -> None:
        self.bus.emit(type_, data)

    def on_verdict(self, v: Verdict) -> None:
        with self.lock:
            self.verdicts.append(v)
        self.emit("verdict", v.model_dump(mode="json"))

    def make_engine(self, oath: Oath) -> Engine:
        self.engine = Engine(oath=oath, ctx=self.ctx, on_verdict=self.on_verdict, judge_enabled=self.cfg.judge_enabled)
        return self.engine

    def over_budget(self) -> bool:
        s = get_settings()
        return self.meter.cost_usd(s.prices) > s.budget.usd_per_story

    def degrade(self, what: str, why: str, fallback: str, index: int | None = None) -> None:
        row = {"what": what, "why": why, "fallback": fallback, **({"index": index} if index else {})}
        with self.lock:
            self.degradations.append(row)
        self.emit("degraded", row)


# ---- graph ---------------------------------------------------------------------------------------------------------------


def build_graph(run: Run):
    cfg = run.cfg
    st = get_settings()
    lesson = lessons.get(cfg.lesson_id)
    n_pages = st.thresholds.pages
    max_rep = st.thresholds.max_repair_attempts
    run.ctx.lesson, run.ctx.age, run.ctx.seed = lesson, cfg.age, cfg.seed
    run.ctx.pages_total, run.ctx.max_correct_slot_share = n_pages, st.thresholds.max_correct_slot_share

    def n_intake(_: S) -> S:
        run.emit(
            "run.started",
            {"story_id": run.story_id, "arm": cfg.arm, "lesson_id": cfg.lesson_id, "age": cfg.age, "seed": cfg.seed,
             "input_hash": run.drawing.sha256[:16]},
        )  # fmt: skip
        return {"halt": None, "pages": [], "i": 1, "notes": []}

    @tracing.span(kind="TOOL", name="node.safety")
    def n_safety(_: S) -> S:
        r = safety.screen(run.drawing)
        run.safety_result = r
        run.ignored = list(r.ignored_text)
        run.ctx.ignored_text = list(r.ignored_text)
        shown = [("personal details (hidden)" if t == safety.PLACEHOLDER else t) for t in r.ignored_text]
        run.emit(
            "safety.result",
            {"tier": r.tier, "action": r.action, "ignored_text": shown, "reason_code": r.reason_code},
        )
        if r.action == "refuse":
            run.outcome = "refused"
            run.emit(
                "run.refused",
                {"reason_code": r.reason_code, "message": CALM_REFUSAL, "trace_id": tracing.current_trace_id()},
            )
            return {"halt": "refused"}
        if r.action == "ask_redraw":
            run.outcome = "ask_redraw"
            run.emit(
                "run.refused",
                {"reason_code": r.reason_code, "message": CALM_REDRAW, "trace_id": tracing.current_trace_id()},
            )
            return {"halt": "ask_redraw"}
        return {}

    @tracing.span(kind="AGENT", name="node.character")
    def n_character(_: S) -> S:
        hero = character.clean_hero_name(cfg.hero_name)
        card, _u = character.build_card(run.drawing, hero)
        run.ctx.card = card
        eng = run.make_engine(catalog.core_oath())  # run-scope checks use the core; the full oath follows
        for attempt in range(2):
            vs = eng.verify_run(card, attempt)
            bad = [v for v in vs if eng.gate(v) != "accept"]
            if not bad:
                break
            if attempt == 0:
                run.repairs.append({"stage": "character", "failed": [v.commitment for v in bad]})
                run.emit("scene.repair", {"index": 0, "attempt": 1, "failed": [v.commitment for v in bad],
                                          "because": "; ".join(v.actual for v in bad)})  # fmt: skip
                card, _u = character.build_card(run.drawing, hero)
                if any(v.commitment == "original_character_only" for v in bad):
                    card = card.model_copy(update={"name": "Pip", "one_line": ""})
                run.ctx.card = card
            else:
                run.shipped.append({"commitment": bad[0].commitment, "scope": "run"})
        run.emit("character.ready", {"card": card.model_dump()})
        return {"card": card}

    @tracing.span(kind="AGENT", name="node.oath")
    def n_oath(s: S) -> S:
        oath, info = oath_author.author(lesson, s["card"])
        run.engine.oath = oath
        plain = {c.id: c.plain for c in oath.commitments}
        run.emit(
            "oath.ready",
            {"oath_hash": oath.hash, "added": info["added"], "rejected": info["rejected"],
             "commitments": [{"id": c.id, "scope": c.scope, "title": c.title, "plain": plain[c.id], "core": c.core,
                              "verifier": c.verifier} for c in oath.commitments]},
        )  # fmt: skip
        return {"oath": oath}

    @tracing.span(kind="AGENT", name="node.plan")
    def n_plan(s: S) -> S:
        beats, _u = planner.plan(lesson, s["card"], cfg.age, n_pages)
        # seeded, balanced placement of the correct answer: half in each slot, shuffled
        slots = [0, 1] * (n_pages // 2)
        rng(cfg.seed, "slots").shuffle(slots)
        run.emit("plan.ready", {"beats": [planner.beat_text(b) for b in beats]})
        return {"beats": beats, "slots": slots}

    # ---- B1 scene loop ------------------------------------------------------------------------------------------------

    @tracing.span(kind="AGENT", name="node.write")
    def n_write(s: S) -> S:
        i = s["i"]
        run.emit("scene.started", {"index": i, "attempt": 0})
        page, _u = writer.write_scene(
            index=i, beat=planner.beat_text(s["beats"][i - 1]), lesson=lesson, card=s["card"], oath=s["oath"],
            pages=s["pages"], age=cfg.age, correct_slot=s["slots"][i - 1],
        )  # fmt: skip
        return {"pending": page, "attempt": 0, "regens": 0}

    @tracing.span(kind="CHAIN", name="node.verify")
    def n_verify(s: S) -> S:
        eng = run.engine
        if run.over_budget() and not eng.rates:
            eng.rates = {"quality": 0.0, "image": 0.0}
            run.degrade("judge", "per-story budget reached", "quality judging off; safety checks unchanged")
        vs = eng.verify_scene(s["pending"], s["attempt"])
        gates = [(v, eng.gate(v)) for v in vs]
        crit = [v for v, g in gates if g == "critical"]
        rep = [v for v, g in gates if g == "repair"]
        if crit:
            route = "regen" if s["regens"] < 1 else "stop"
        elif rep:
            route = "repair" if s["attempt"] < max_rep else "accept_noted"
        else:
            route = "accept"
        return {"vs": crit or rep or vs, "route": route}

    def failing_info(vs: list[Verdict]) -> dict:
        bad = [v for v in vs if not v.ok or v.status == "verification_error"]
        oath = run.engine.oath
        hints = {c.id: c.repair_hint for c in oath.commitments}
        return {
            "commitment": ", ".join(v.commitment for v in bad),
            "expected": " ".join(v.expected for v in bad),
            "actual": " ".join(v.actual for v in bad),
            "hint": " ".join(h for h in (hints.get(v.commitment, "") for v in bad) if h),
        }

    @tracing.span(kind="AGENT", name="node.repair")
    def n_repair(s: S) -> S:
        i, attempt = s["i"], s["attempt"] + 1
        info = failing_info(s["vs"])
        run.repairs.append({"stage": "scene", "index": i, "attempt": attempt, "failed": info["commitment"]})
        run.emit(
            "scene.repair",
            {"index": i, "attempt": attempt, "failed": info["commitment"].split(", "), "because": info["actual"]},
        )
        page, _u = writer.repair_scene(
            page=s["pending"], beat=planner.beat_text(s["beats"][i - 1]), lesson=lesson, card=s["card"],
            attempt=attempt, age=cfg.age, correct_slot=s["slots"][i - 1], **info,
        )  # fmt: skip
        run.emit("scene.started", {"index": i, "attempt": attempt})
        return {"pending": page, "attempt": attempt}

    @tracing.span(kind="AGENT", name="node.regen")
    def n_regen(s: S) -> S:
        """Tier C: our own output tripped a safety check. Quarantine the page and write it again once."""
        i, attempt = s["i"], s["attempt"] + 1
        run.repairs.append({"stage": "scene", "index": i, "attempt": attempt, "failed": "safety", "regen": True})
        run.emit("scene.repair", {"index": i, "attempt": attempt, "failed": [v.commitment for v in s["vs"]],
                                  "because": "page quarantined; writing it again"})  # fmt: skip
        page, _u = writer.write_scene(
            index=i, beat=planner.beat_text(s["beats"][i - 1]), lesson=lesson, card=s["card"], oath=s["oath"],
            pages=s["pages"], age=cfg.age, correct_slot=s["slots"][i - 1], temperature=0.95,
        )  # fmt: skip
        run.emit("scene.started", {"index": i, "attempt": attempt})
        return {"pending": page, "attempt": attempt, "regens": s["regens"] + 1}

    def n_stop(s: S) -> S:
        run.outcome = "stopped"
        run.emit(
            "run.refused", {"reason_code": "unsafe_story", "message": CALM_STOP, "trace_id": tracing.current_trace_id()}
        )
        return {"halt": "stopped"}

    def accept(s: S, noted: bool) -> S:
        page = s["pending"]
        if noted:
            for v in s["vs"]:
                if not v.ok:
                    run.shipped.append({"commitment": v.commitment, "scope": v.scope, "actual": v.actual})
        pages = [*s["pages"], page]
        run.ctx.pages = pages
        run.emit("scene.accepted", {"index": page.index, "attempts_used": s["attempt"], "page": _public_page(page)})
        return {"pages": pages, "i": s["i"] + 1}

    def n_accept(s: S) -> S:
        return accept(s, False)

    def n_accept_noted(s: S) -> S:
        return accept(s, True)

    def after_accept(s: S) -> str:
        return "story_gate" if s["i"] > n_pages else "write"

    # ---- B0: one call, evaluate afterwards ----------------------------------------------------------------------------

    @tracing.span(kind="AGENT", name="node.baseline")
    def n_baseline(s: S) -> S:
        pages, _u = writer.baseline_story(lesson=lesson, card=s["card"], age=cfg.age, n=n_pages)
        run.ctx.pages = pages
        eng = run.engine
        for p in pages:
            run.emit("scene.started", {"index": p.index, "attempt": 0})
            vs = eng.verify_scene(p, 0) if p.choices else []
            for v in vs:
                if not v.ok:
                    run.shipped.append({"commitment": v.commitment, "scope": v.scope, "actual": v.actual})
            run.emit("scene.accepted", {"index": p.index, "attempts_used": 0, "page": _public_page(p)})
        return {"pages": pages}

    # ---- story gate ---------------------------------------------------------------------------------------------------

    def rebalance(pages: list[Page]) -> list[Page]:
        """Programmatic repair: swap choice order on the fewest pages so no slot holds the answer on more than 5."""
        slots = [next((k for k, c in enumerate(p.choices) if c.is_correct), 0) for p in pages]
        cap = st.thresholds.max_correct_slot_share
        for slot in (0, 1):
            idx = [k for k, v in enumerate(slots) if v == slot]
            for k in idx[cap:]:
                pages[k].choices = list(reversed(pages[k].choices))
                for c, cid in zip(pages[k].choices, "ab", strict=False):
                    c.id = cid
                slots[k] = 1 - slot
        return pages

    @tracing.span(kind="CHAIN", name="node.story_gate")
    def n_story_gate(s: S) -> S:
        eng, pages = run.engine, list(s["pages"])
        card = s["card"]
        rounds = 1 if cfg.arm == "B0" else 2
        for rnd in range(rounds + 1):
            run.ctx.pages = pages
            vs = eng.verify_story(pages, rnd)
            bad = [v for v in vs if eng.gate(v) != "accept"]
            if not bad or cfg.arm == "B0" or rnd == rounds:
                for v in bad:
                    run.shipped.append({"commitment": v.commitment, "scope": v.scope, "actual": v.actual})
                break
            for v in bad:
                run.repairs.append({"stage": "story", "attempt": rnd + 1, "failed": v.commitment})
                run.emit(
                    "scene.repair", {"index": 0, "attempt": rnd + 1, "failed": [v.commitment], "because": v.actual}
                )
                if v.commitment == "correct_choice_position_balanced":
                    pages = rebalance(pages)
                    continue
                target = v.evidence.scene
                if target is None and v.evidence.quote:
                    target = next(
                        (p.index for p in pages if norm_ws(v.evidence.quote) in norm_ws(p.review_text())), None
                    )
                if target is None:
                    target = pages[-1].index
                p = pages[target - 1]
                new, _u = writer.repair_scene(
                    page=p, beat=planner.beat_text(s["beats"][target - 1]), lesson=lesson, card=card,
                    commitment=v.commitment, expected=v.expected, actual=v.actual,
                    hint=eng.get(v.commitment).repair_hint or "Make this page clearly teach the lesson and differ from the others.",
                    attempt=rnd + 1, age=cfg.age, correct_slot=s["slots"][target - 1],
                )  # fmt: skip
                pages[target - 1] = new
                for sv in eng.verify_scene(new, rnd + 1):
                    if eng.gate(sv) == "critical":
                        pages[target - 1] = p  # keep the page that was already accepted
        return {"pages": pages}

    # ---- media --------------------------------------------------------------------------------------------------------

    def save(kind: str, index: int, data: bytes, ext: str) -> str:
        if not cfg.run_dir:
            return ""
        path = cfg.run_dir / "pages" / str(index) / f"{kind}.{ext}"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return str(path)

    def one_image(p: Page, card: CharacterCard) -> None:
        eng = run.engine
        prompt = p.image_prompt
        vp = eng.verify_image_prompt(p, 0)
        if any(not v.ok for v in vp):  # cheap programmatic repair: name the hero and one trait
            prompt = f"{card.name} the {card.species}, {card.traits[0] if card.traits else ''}. {prompt}"
            p = p.model_copy(update={"image_prompt": prompt})
            eng.verify_image_prompt(p, 1)
        data, mime, err = None, "image/png", ""
        for attempt in range(2):
            try:
                r = images.illustrate(prompt, reference=(run.drawing.data, run.drawing.mime))
                data, mime = r.value, r.raw_text or "image/png"
            except ClientError as e:
                data = None
                err = str(e)[:120]
            vs = eng.verify_image(p, data, mime, attempt)
            if all(v.ok for v in vs):
                break
            if attempt == 0:
                run.emit("scene.repair", {"index": p.index, "attempt": 1, "failed": [v.commitment for v in vs if not v.ok],
                                          "because": "picture did not pass; painting it once more"})  # fmt: skip
        ok_present = data is not None and d.illustration_present(data, run.ctx).status == "pass"
        if not ok_present:
            run.degrade("image", err or "no valid picture returned", "text only", p.index)
            return
        for v in vs:
            if not v.ok:
                run.shipped.append({"commitment": v.commitment, "scope": v.scope, "actual": v.actual})
        ext = "jpg" if "jpeg" in mime else "png"
        path = save("image", p.index, data, ext)
        with run.lock:
            run.media_paths[f"image:{p.index}"] = path
        run.emit("image.ready", {"index": p.index, "url": f"/api/stories/{run.story_id}/pages/{p.index}/image",
                                 "verdict": "pass" if all(v.ok for v in vs) else "warning"})  # fmt: skip

    def one_audio(p: Page) -> None:
        eng = run.engine
        data = None
        err = ""
        for attempt in range(2):
            try:
                data = tts.narrate(p.narration_text or f"{p.scenario} {p.question}").value
            except ClientError as e:
                data, err = None, str(e)[:120]
            vs = eng.verify_audio(p, data, attempt)
            if all(v.ok for v in vs):
                break
        if data is None or not all(v.ok for v in vs):
            run.degrade("audio", err or "audio did not pass the check", "text only", p.index)
            return
        path = save("audio", p.index, data, "mp3")
        with run.lock:
            run.media_paths[f"audio:{p.index}"] = path
        run.emit("audio.ready", {"index": p.index, "url": f"/api/stories/{run.story_id}/pages/{p.index}/audio",
                                 "seconds": round(len(data) * 8 / 48_000, 1)})  # fmt: skip

    @tracing.span(kind="CHAIN", name="node.media")
    def n_media(s: S) -> S:
        if not cfg.media:
            return {}
        pages, card = s["pages"], s["card"]
        jobs = [(one_image, p, card) for p in pages] + [(one_audio, p) for p in pages]
        with cf.ThreadPoolExecutor(max_workers=4) as pool:
            futs = []
            for fn, *a in jobs:
                ctx = contextvars.copy_context()  # keep the trace parent and the usage meter
                futs.append(pool.submit(ctx.run, fn, *a))
            for f in futs:
                try:
                    f.result()
                except Exception as e:  # one broken page must not sink the story
                    run.degrade("check", f"media worker failed: {type(e).__name__}", "page shown without media")
        return {}

    # ---- receipt ------------------------------------------------------------------------------------------------------

    @tracing.span(kind="CHAIN", name="node.receipt")
    def n_receipt(s: S) -> S:
        run.receipt = make_receipt(run, s)
        run.emit("receipt", run.receipt)
        run.outcome = "shipped" if not run.shipped else "shipped_with_notes"
        run.emit("run.finished", {"outcome": run.outcome, "story_id": run.story_id})
        return {}

    # ---- wiring -------------------------------------------------------------------------------------------------------

    def halted(s: S) -> str:
        return "end" if s.get("halt") else "go"

    g = StateGraph(S)
    for name, fn in [("intake", n_intake), ("safety", n_safety), ("character", n_character), ("oath", n_oath),
                     ("plan", n_plan), ("write", n_write), ("verify", n_verify), ("repair", n_repair),
                     ("regen", n_regen), ("stop", n_stop), ("accept", n_accept), ("accept_noted", n_accept_noted),
                     ("baseline", n_baseline), ("story_gate", n_story_gate), ("media", n_media),
                     ("receipt", n_receipt)]:  # fmt: skip
        g.add_node(name, fn)
    g.set_entry_point("intake")
    g.add_edge("intake", "safety")
    g.add_conditional_edges("safety", halted, {"end": END, "go": "character"})
    g.add_edge("character", "oath")
    g.add_edge("oath", "plan")
    g.add_conditional_edges(
        "plan", lambda s: "baseline" if cfg.arm == "B0" else "write", {"baseline": "baseline", "write": "write"}
    )
    g.add_edge("write", "verify")
    g.add_conditional_edges("verify", lambda s: s["route"],
                            {"accept": "accept", "accept_noted": "accept_noted", "repair": "repair", "regen": "regen", "stop": "stop"})  # fmt: skip
    g.add_edge("repair", "verify")
    g.add_edge("regen", "verify")
    g.add_edge("stop", END)
    for a in ("accept", "accept_noted"):
        g.add_conditional_edges(a, after_accept, {"story_gate": "story_gate", "write": "write"})
    g.add_edge("baseline", "story_gate")
    g.add_edge("story_gate", "media")
    g.add_edge("media", "receipt")
    g.add_edge("receipt", END)
    return g.compile()


# ---- receipt -------------------------------------------------------------------------------------------------------------


def make_receipt(run: Run, s: S) -> dict[str, Any]:
    st = get_settings()
    oath = s["oath"]
    latest: dict[tuple[str, str], Verdict] = {}
    for v in run.verdicts:
        latest[(v.commitment, v.scope)] = v
    by_commitment: dict[str, list[Verdict]] = {}
    for (cid, _scope), v in latest.items():
        by_commitment.setdefault(cid, []).append(v)
    checked = {cid for cid, vs in by_commitment.items() if any(v.status != "skipped" for v in vs)}
    kept = {cid for cid in checked if all(v.ok for v in by_commitment[cid])}
    broken = sorted(checked - kept)
    first_fail = {(v.commitment, v.scope) for v in run.verdicts if v.status in ("violation", "critical")}
    n_checks = sum(1 for v in run.verdicts if v.status != "skipped")
    repairs = len(run.repairs)
    rewritten = len({(r.get("index"), r.get("stage")) for r in run.repairs if r.get("stage") == "scene"})
    if run.cfg.arm == "B0":
        plain = f"{len(checked)} promises checked afterwards. {len(broken)} broken. Nothing was repaired (observe-only run)."
    elif broken:
        plain = f"{len(checked)} promises checked. {rewritten} pages rewritten. {len(broken)} could not be fully kept: {', '.join(broken)}."
    else:
        plain = f"{len(checked)} promises checked. {rewritten} pages rewritten. All kept."
    totals = run.meter.totals()
    ignored = ["personal details (hidden)" if t == safety.PLACEHOLDER else t for t in run.ignored if _worth_listing(t)]
    attempts = {}
    for v in run.verdicts:
        if v.scope.startswith("scene "):
            i = int(v.scope.split()[1])
            attempts[i] = max(attempts.get(i, 0), v.attempt)
    pages = [{"index": i, "attempts": a + 1, "final": "pass"} for i, a in sorted(attempts.items())]
    for sh in run.shipped:
        for p in pages:
            if sh["scope"] == f"scene {p['index']}":
                p["final"] = "noted"
    cov = coverage(oath)
    return {
        "story_id": run.story_id,
        "oath_hash": oath.hash,
        "arm": run.cfg.arm,
        "plain": plain,
        "counts": {
            "commitments": len(oath.commitments), "checked": len(checked), "checks": n_checks,
            "violations_found": len(first_fail), "repairs": repairs, "kept": len(kept),
            "shipped_violations": len(run.shipped), "judge_enabled": run.cfg.judge_enabled,
        },
        "broken": broken,
        "pages": pages,
        "coverage": cov,
        "degradations": run.degradations,
        "ignored_drawing_text": ignored,
        "budget": {
            "usd_estimate": run.meter.cost_usd(st.prices), "estimate": True, "seconds": round(_now() - run.t0, 1),
            "tokens_in": totals["tokens_in"], "tokens_out": totals["tokens_out"], "images": totals["images"],
            "calls": totals["calls"], "by_model": totals["by_model"],
        },
        "prompt_version": prompts.VERSION,
        "models": {"writer": st.models.writer, "judge": st.models.judge, "vision": st.models.vision},
        "trace_id": run.trace_id,
        "generated_at": ledger.now_ist().isoformat(timespec="seconds"),
    }  # fmt: skip


def _worth_listing(t: str) -> bool:
    return bool(t.strip())


def _now() -> float:
    import time

    return time.time()


# ---- entry point ---------------------------------------------------------------------------------------------------------


def execute(run: Run) -> Run:
    """Run the graph to the end under one WORKFLOW trace. Never raises: an unexpected error becomes an `error` event."""
    run.t0 = _now()

    @tracing.span(kind="WORKFLOW", name="create-storybook")
    def _go() -> None:
        run.trace_id = tracing.current_trace_id()
        graph = build_graph(run)
        with metered() as meter:
            run.meter = meter
            graph.invoke({}, {"recursion_limit": 200})

    try:
        _go()
    except Exception as e:
        run.outcome = run.outcome or "error"
        run.emit("error", {"code": "internal", "message": "Something went wrong while making the story."})
        run.error = f"{type(e).__name__}: {e}"[:300]
    finally:
        if run.cfg.ledger_name:
            ledger.append(ledger_row(run))
        run.bus.close()
        tracing.flush()
    return run


def ledger_row(run: Run) -> dict:
    r = run.receipt or {}
    return {
        "name": run.cfg.ledger_name, "story_id": run.story_id, "fixture": run.cfg.fixture, "lesson": run.cfg.lesson_id,
        "arm": run.cfg.arm, "seed": run.cfg.seed, "age": run.cfg.age, "outcome": run.outcome, "trace_id": run.trace_id,
        "oath_hash": r.get("oath_hash"), "counts": r.get("counts"), "broken": r.get("broken"),
        "shipped": run.shipped, "degradations": run.degradations, "budget": r.get("budget"),
        "error": run.error or None,
    }  # fmt: skip
