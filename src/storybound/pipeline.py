"""The story run as a LangGraph state machine.

intake -> safety -> character -> oath -> plan -> [write -> verify -> (repair | regen | accept)]x8 -> story gate -> media -> receipt

Arm B1 gates and repairs inside the run. Arm B0 (observe-only) writes the story in one call and only evaluates it
afterwards; nothing is gated or repaired. Both arms share the safety screen, the character card and the oath, so the
only thing that differs is whether verification is allowed to change the outcome.
"""

from __future__ import annotations

import concurrent.futures as cf
import contextvars
import json
import os
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from . import chaos, ledger, lessons, prompts, tracing
from . import media as media_mod
from .agents import character, oath_author, planner, quizmaker, safety, writer
from .agents.common import rng
from .clients import images, tts
from .clients.errors import ClientError
from .clients.usage import Meter, metered
from .config import get_settings
from .events import EventLog
from .media import Drawing
from .models import CharacterCard, Oath, Page, Quiz, Verdict
from .oath import catalog
from .oath import deterministic as d
from .oath.engine import Engine, coverage
from .textutil import norm_ws

CALM_REFUSAL = "This drawing isn't one I can turn into a story. Could we try a different picture together?"
CALM_REDRAW = "I couldn't quite see a hero in that picture. Could you draw one a little bigger and darker?"
OBSERVE = ("B0", "B2")  # arms where verification only observes: nothing is gated or repaired by the oath
IMAGE_SLOTS = threading.BoundedSemaphore(2)
MAX_AHEAD = int(os.environ.get("STORYBOUND_MAX_AHEAD", "3"))  # pages written ahead of the oldest page under review; 1 = sequential (ablation)
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
    judge_fn: Any = None  # tests inject a fake judge; None means the K2 judge
    pictures: str = "full"  # illustration policy from the cfo.ai model: full (every page), half (pages 1, 3, 5, 7), none, or auto (the agent picks the pages that matter most within a picture budget)
    quiz: bool = True  # gated arm only: a verified quiz after the story
    grownup_promises: tuple[str, ...] = ()  # a parent's or teacher's own promises, already cleaned


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
    inflight: list[dict]


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
    root_ctx: Any = None  # the context of the workflow span (see task_context)
    picture_plan: dict | None = None  # the pages the agent chose to paint, and why (policy "auto")
    image_failures: int = 0  # picture calls that failed in a row; two in a row stop the painting of the rest
    plan_announced: bool = False  # the picture plan was announced as soon as the story was planned
    paint_set: set[int] = field(default_factory=set)  # pages that will get a picture, known before the pages are written
    early: dict[int, tuple[dict, Any]] = field(default_factory=dict)  # page index -> (page as painted, its future): pictures start as pages are accepted
    t0: float = 0.0
    media_paths: dict[str, str] = field(default_factory=dict)
    quiz: Quiz | None = None
    quiz_stats: dict = field(default_factory=dict)  # questions made and kept, for the ledger
    forgotten: bool = False  # the parent asked to forget this story: nothing more is written to disk
    lock: threading.Lock = field(default_factory=threading.Lock)

    # ---- helpers ------------------------------------------------------------------------------------------------------

    def emit(self, type_: str, data: dict | None = None) -> None:
        self.bus.emit(type_, data)

    def on_verdict(self, v: Verdict) -> None:
        with self.lock:
            self.verdicts.append(v)
        self.emit("verdict", v.model_dump(mode="json"))

    def make_engine(self, oath: Oath) -> Engine:
        self.engine = Engine(
            oath=oath,
            ctx=self.ctx,
            on_verdict=self.on_verdict,
            judge_enabled=self.cfg.judge_enabled,
            defer_judge_on_det_fail=self.cfg.arm == "B1",
            task_context=self.task_context,
            **({"judge": self.cfg.judge_fn} if self.cfg.judge_fn else {}),
        )
        return self.engine

    def task_context(self) -> contextvars.Context:
        """The context for a worker thread. A node span ends when the node returns, but a judge call or a picture started in it keeps running; a span
        whose parent has already ended is exported by neatlogs as a trace of its own (found in HR-014: 2 of 4 pictures and every picture check
        were missing from the story's trace). Starting such work from the workflow's own context keeps every span in the one trace."""
        return self.root_ctx.copy() if self.root_ctx is not None else contextvars.copy_context()

    def painting_should_stop(self) -> str:
        """Why the agent stops painting the rest (only when it chose the pages itself): the picture service keeps failing, or the budget is gone."""
        if self.cfg.pictures != "auto":
            return ""
        if self.image_failures >= 2:
            return "the picture service failed twice in a row"
        if self.over_budget():
            return "the story's budget is used up"
        return ""

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
        if r.reason_code == "screen_unavailable":  # our service failed, not the drawing: never tell a child their picture was refused
            return unavailable("the safety screen could not run")
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

    def unavailable(why: str) -> S:
        """A service we depend on failed. The child sees the soft "try again" screen, never a refusal; the ledger says error."""
        run.outcome = "error"
        run.error = f"service unavailable: {why}"
        run.emit("error", {"code": "service_unavailable", "message": "Pip is having trouble right now. Please try again in a minute."})
        return {"halt": "error"}

    @tracing.span(kind="AGENT", name="node.character")
    def n_character(_: S) -> S:
        hero = character.clean_hero_name(cfg.hero_name)
        card, _u = character.build_card(run.drawing, hero, cfg.seed)
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
                card, _u = character.build_card(run.drawing, hero, cfg.seed)
                if any(v.commitment == "original_character_only" for v in bad):
                    card = card.model_copy(update={"name": "Pip", "one_line": ""})
                run.ctx.card = card
            else:
                run.shipped.append({"commitment": bad[0].commitment, "scope": "run"})
        run.emit("character.ready", {"card": card.model_dump()})
        return {"card": card}

    @tracing.span(kind="AGENT", name="node.oath")
    def n_oath(s: S) -> S:
        """Write the oath. In the gated arm the story plan is made at the same time: it needs only the card."""
        pool, fut = None, None
        if cfg.arm == "B1":
            pool = cf.ThreadPoolExecutor(max_workers=1)
            fut = pool.submit(contextvars.copy_context().run, planner.plan, lesson, s["card"], cfg.age, n_pages)
        oath, info = oath_author.author(lesson, s["card"])
        if cfg.grownup_promises:
            oath = catalog.merge_grownup(oath, list(cfg.grownup_promises))
        if cfg.arm == "B1" and cfg.quiz:
            oath = catalog.with_quiz(oath)
        run.engine.oath = oath
        plain = {c.id: c.plain for c in oath.commitments}
        run.emit(
            "oath.ready",
            {"oath_hash": oath.hash, "added": info["added"], "rejected": info["rejected"],
             "commitments": [{"id": c.id, "scope": c.scope, "title": c.title, "plain": plain[c.id], "core": c.core,
                              "verifier": c.verifier} for c in oath.commitments]},
        )  # fmt: skip
        out: S = {"oath": oath}
        if fut is not None and pool is not None:
            beats, _u = fut.result()
            pool.shutdown()
            # seeded, balanced placement of the correct answer: half in each slot, shuffled
            slots = [0, 1] * (n_pages // 2)
            rng(cfg.seed, "slots").shuffle(slots)
            run.emit("plan.ready", {"beats": [planner.beat_text(b) for b in beats]})
            if early_painting:  # decide the pictures now, so they can be painted while the child is still reading
                imp = {b["index"]: b.get("importance", 1) for b in beats}
                order = picture_order(cfg.pictures, list(range(1, n_pages + 1)), imp, st.budget.pictures_usd_per_story, st.prices.image_each)
                announce_paint_plan(imp, order, list(range(1, n_pages + 1)))
            out.update({"beats": beats, "slots": slots})
        return out

    # ---- B1 scene loop ------------------------------------------------------------------------------------------------
    # Pages are written ahead while the slow judge reviews earlier ones (at most MAX_AHEAD in flight). A page is shown
    # (scene.accepted) only after its review is back and clean, in order. If a review fails, everything written after
    # that page is thrown away and the page is repaired, so verification still gates what the child can see.

    def chain(s: S) -> list[Page]:
        return [*s["pages"], *[e["page"] for e in s.get("inflight", [])]]

    @tracing.span(kind="AGENT", name="node.write")
    def n_write(s: S) -> S:
        i = s["i"]
        run.emit("scene.started", {"index": i, "attempt": 0})
        page, _u = writer.write_scene(
            index=i, beat=planner.beat_text(s["beats"][i - 1]), lesson=lesson, card=s["card"], oath=s["oath"],
            pages=chain(s), age=cfg.age, correct_slot=s["slots"][i - 1],
        )  # fmt: skip
        return {"pending": page, "attempt": 0, "regens": 0}

    def decide(vs: list[Verdict], attempt: int, regens: int) -> str:
        eng = run.engine
        gates = [(v, eng.gate(v)) for v in vs]
        if any(g == "critical" for _, g in gates):
            return "regen" if regens < 1 else "stop"
        if any(g == "repair" for _, g in gates):
            return "repair" if attempt < max_rep else "accept_noted"
        return "accept"

    def bad_first(vs: list[Verdict]) -> list[Verdict]:
        eng = run.engine
        crit = [v for v in vs if eng.gate(v) == "critical"]
        rep = [v for v in vs if eng.gate(v) == "repair"]
        return crit or rep or vs

    @tracing.span(kind="CHAIN", name="node.verify")
    def n_verify(s: S) -> S:
        eng, page, attempt = run.engine, s["pending"], s["attempt"]
        if run.over_budget() and not eng.rates:
            eng.rates = {"quality": 0.0, "image": 0.0}
            run.degrade("judge", "per-story budget reached", "quality judging off; safety checks unchanged")
        pend = eng.verify_scene_async(page, attempt)
        if pend.det_failed and attempt < max_rep:  # a cheap check failed: repair now, judge after the repair
            vs = pend.result()
            route = decide(vs, attempt, s["regens"])
            if route in ("repair", "regen", "stop"):
                return {"vs": bad_first(vs), "route": route}
            # nothing blocking (for example a quality check that could not run): carry on like a clean page
        entry = {"page": page, "attempt": attempt, "regens": s["regens"], "pend": pend}
        return {"inflight": [*s.get("inflight", []), entry], "i": s["i"] + 1, "route": "submit"}

    def n_submit(s: S) -> S:
        return {}

    def after_submit(s: S) -> str:
        return "settle" if len(s["inflight"]) >= MAX_AHEAD or s["i"] > n_pages else "write"

    @tracing.span(kind="CHAIN", name="node.settle")
    def n_settle(s: S) -> S:
        """Wait for the oldest review. Clean: show the page. Not clean: roll back to it and repair."""
        head, rest = s["inflight"][0], s["inflight"][1:]
        page, attempt, regens = head["page"], head["attempt"], head["regens"]
        vs = head["pend"].result()
        route = decide(vs, attempt, regens)
        if route in ("accept", "accept_noted"):
            if route == "accept_noted":
                for v in vs:
                    if not v.ok:
                        run.shipped.append({"commitment": v.commitment, "scope": v.scope, "actual": v.actual})
            pages = [*s["pages"], page]
            run.ctx.pages = pages
            run.emit("scene.accepted", {"index": page.index, "attempts_used": attempt, "page": _public_page(page)})
            start_painting(page, s["card"])
            if not rest and s["i"] > n_pages:
                nxt = "story_gate"
            elif rest and (len(rest) >= MAX_AHEAD or s["i"] > n_pages):
                nxt = "settle"
            else:
                nxt = "write"
            return {"pages": pages, "inflight": rest, "route": nxt}
        # roll back: pages written after this one are discarded; this page goes round the repair loop
        return {"inflight": [], "i": page.index, "pending": page, "attempt": attempt, "regens": regens,
                "vs": bad_first(vs), "route": route}  # fmt: skip

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
        i, attempt = s["pending"].index, s["attempt"] + 1
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
        i, attempt = s["pending"].index, s["attempt"] + 1
        run.repairs.append({"stage": "scene", "index": i, "attempt": attempt, "failed": "safety", "regen": True})
        run.emit("scene.repair", {"index": i, "attempt": attempt, "failed": [v.commitment for v in s["vs"]],
                                  "because": "page quarantined; writing it again"})  # fmt: skip
        page, _u = writer.write_scene(
            index=i, beat=planner.beat_text(s["beats"][i - 1]), lesson=lesson, card=s["card"], oath=s["oath"],
            pages=chain(s), age=cfg.age, correct_slot=s["slots"][i - 1], temperature=0.95,
        )  # fmt: skip
        run.emit("scene.started", {"index": i, "attempt": attempt})
        return {"pending": page, "attempt": attempt, "regens": s["regens"] + 1}

    def n_stop(s: S) -> S:
        if s.get("vs") and all(v.status == "verification_error" for v in s["vs"]):  # nothing unsafe was found: the checkers were down
            return unavailable("the safety judges could not run")
        run.outcome = "stopped"
        run.emit(
            "run.refused", {"reason_code": "unsafe_story", "message": CALM_STOP, "trace_id": tracing.current_trace_id()}
        )
        return {"halt": "stopped"}

    # ---- B0: one call, evaluate afterwards ----------------------------------------------------------------------------

    @tracing.span(kind="AGENT", name="node.baseline")
    def n_baseline(s: S) -> S:
        pages, _u = writer.baseline_story(lesson=lesson, card=s["card"], age=cfg.age, n=n_pages)
        if cfg.arm == "B2":  # the general-purpose-agent baseline: the same model reviews and fixes its own story
            pages = writer.self_critique(pages, lesson=lesson, card=s["card"], age=cfg.age)
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
        before = [p.model_dump() for p in s["pages"]]  # rebalancing edits pages in place
        card = s["card"]
        rounds = 1 if cfg.arm in OBSERVE else 2
        for rnd in range(rounds + 1):
            run.ctx.pages = pages
            vs = eng.verify_story(pages, rnd)
            bad = [v for v in vs if eng.gate(v) != "accept"]
            if not bad or cfg.arm in OBSERVE or rnd == rounds:
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
        for old, new in zip(before, pages, strict=False):
            if old != new.model_dump():  # the story gate rewrote or reordered this page
                run.emit(
                    "scene.accepted",
                    {"index": new.index, "attempts_used": 0, "page": _public_page(new), "revised": True},
                )
        return {"pages": pages}

    # ---- media --------------------------------------------------------------------------------------------------------

    def save(kind: str, index: int, data: bytes, ext: str) -> str:
        if not cfg.run_dir or run.forgotten:
            return ""
        path = cfg.run_dir / "pages" / str(index) / f"{kind}.{ext}"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return str(path)

    early_painting = cfg.media and cfg.arm == "B1" and cfg.pictures != "none"
    early_pool = cf.ThreadPoolExecutor(max_workers=2) if early_painting else None

    def announce_paint_plan(imp: dict[int, int], order: list[int], indices: list[int]) -> None:
        """Say which pages will be painted (and why the others will not) as soon as the story is planned."""
        run.paint_set = set(order)
        run.plan_announced = True
        if cfg.pictures == "auto":
            run.picture_plan = {"painted": sorted(order), "importance": imp, "budget_usd": st.budget.pictures_usd_per_story}
            run.emit("paint.plan", run.picture_plan)
        for i in indices:
            if i not in run.paint_set:  # a plan choice, not a failure: the page keeps its words and its narration
                why = f"the agent kept its picture budget for the pages that matter most (importance {imp.get(i, 1)})"
                run.degrade("image", why if cfg.pictures == "auto" else "this plan paints some pages only", "text only", i)

    def start_painting(p: Page, card: CharacterCard) -> None:
        """A page was just accepted: if it is one of the pages to paint, start its picture now (the child is still reading)."""
        if not early_painting or early_pool is None or p.index not in run.paint_set or run.forgotten:
            return
        ctx = run.task_context()
        run.early[p.index] = (p.model_dump(), early_pool.submit(ctx.run, one_image, p, card))

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
                with IMAGE_SLOTS:  # the image quota is per minute: at most two paintings at once
                    stop = run.painting_should_stop()
                    if stop:  # the last results say painting more would waste the budget or the quota: keep words and voice
                        run.degrade("image", stop, "text only", p.index)
                        return
                    r = images.illustrate(prompt, reference=(run.drawing.data, run.drawing.mime))
                data, mime = r.value, r.raw_text or "image/png"
                run.image_failures = 0
            except ClientError as e:
                data = None
                err = str(e)[:120]
                with run.lock:
                    run.image_failures += 1
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
        try:
            data, ext = media_mod.web_image(data), "jpg"
        except Exception:  # keep the original bytes if re-encoding fails
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

    @tracing.span(kind="AGENT", name="node.quiz")
    def n_quiz(s: S) -> S:
        """A quiz about the finished story. A question that cannot pass its promises is dropped, never shown."""
        if cfg.arm != "B1" or not cfg.quiz or run.engine is None:
            return {}
        pages = s["pages"]
        run.ctx.pages = pages
        try:
            quiz = quizmaker.verified_quiz(run.engine, pages, s["card"], lesson, cfg.age, cfg.seed, max_rep, run.repairs, run.quiz_stats)
        except Exception as e:  # no quiz is better than a broken one: the story itself is already complete
            run.degrade("check", f"quiz maker failed: {type(e).__name__}", "no quiz")
            return {}
        if quiz:
            run.quiz = quiz
            run.emit("quiz.ready", quiz.model_dump())
        else:
            run.degrade("check", "fewer than two questions passed their promises", "no quiz")
        return {}

    @tracing.span(kind="CHAIN", name="node.media")
    def n_media(s: S) -> S:
        if not cfg.media:
            return {}
        pages, card = s["pages"], s["card"]
        imp = {b["index"]: b.get("importance", 1) for b in s.get("beats", [])}
        order = picture_order(cfg.pictures, [p.index for p in pages], imp, st.budget.pictures_usd_per_story, st.prices.image_each)
        by_index = {p.index: p for p in pages}
        if not run.plan_announced:  # the arms that do not paint early (and tests) announce the plan here
            announce_paint_plan(imp, order, [p.index for p in pages])
        # pictures already started while the child read: keep them unless the story gate rewrote that page afterwards
        todo = [i for i in order if i not in run.early or run.early[i][0] != by_index[i].model_dump()]
        jobs = [(one_image, by_index[i], card) for i in todo] + [(one_audio, p) for p in pages]
        with cf.ThreadPoolExecutor(max_workers=4) as pool:
            futs = []
            for fn, *a in jobs:
                ctx = run.task_context()  # keep the trace parent and the usage meter
                futs.append(pool.submit(ctx.run, fn, *a))
            for f in futs + [fut for _snap, fut in run.early.values()]:
                try:
                    f.result()
                except Exception as e:  # one broken page must not sink the story
                    run.degrade("check", f"media worker failed: {type(e).__name__}", "page shown without media")
        if early_pool is not None:
            early_pool.shutdown(wait=True)
        return {}

    # ---- receipt ------------------------------------------------------------------------------------------------------

    @tracing.span(kind="CHAIN", name="node.receipt")
    def n_receipt(s: S) -> S:
        run.receipt = make_receipt(run, s)
        run.emit("receipt", run.receipt)
        run.outcome = "shipped" if not run.shipped else "shipped_with_notes"
        export_story(run, s)
        run.emit("run.finished", {"outcome": run.outcome, "story_id": run.story_id})
        return {}

    # ---- wiring -------------------------------------------------------------------------------------------------------

    def halted(s: S) -> str:
        return "end" if s.get("halt") else "go"

    g = StateGraph(S)
    for name, fn in [("intake", n_intake), ("safety", n_safety), ("character", n_character), ("oath", n_oath),
                     ("write", n_write), ("verify", n_verify), ("submit", n_submit), ("settle", n_settle),
                     ("repair", n_repair), ("regen", n_regen), ("stop", n_stop),
                     ("baseline", n_baseline), ("story_gate", n_story_gate), ("quiz", n_quiz), ("media", n_media),
                     ("receipt", n_receipt)]:  # fmt: skip
        g.add_node(name, fn)
    g.set_entry_point("intake")
    g.add_edge("intake", "safety")
    g.add_conditional_edges("safety", halted, {"end": END, "go": "character"})
    g.add_edge("character", "oath")
    g.add_conditional_edges(
        "oath", lambda s: "write" if cfg.arm == "B1" else "baseline", {"baseline": "baseline", "write": "write"}
    )
    g.add_edge("write", "verify")
    g.add_conditional_edges("verify", lambda s: s["route"],
                            {"submit": "submit", "repair": "repair", "regen": "regen", "stop": "stop",
                             "accept_noted": "submit"})  # fmt: skip
    g.add_conditional_edges("submit", after_submit, {"settle": "settle", "write": "write"})
    g.add_conditional_edges("settle", lambda s: s["route"],
                            {"write": "write", "settle": "settle", "story_gate": "story_gate", "repair": "repair",
                             "regen": "regen", "stop": "stop"})  # fmt: skip
    g.add_edge("repair", "verify")
    g.add_edge("regen", "verify")
    g.add_edge("stop", END)
    g.add_edge("baseline", "story_gate")
    g.add_edge("story_gate", "quiz")
    g.add_edge("quiz", "media")
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
    if run.cfg.arm in OBSERVE:
        plain = f"{len(checked)} promises checked afterwards. {len(broken)} broken. Nothing was repaired by the oath (observe-only run)."
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
        "promises": [
            {
                "id": c.id, "title": c.title, "plain": c.plain, "scope": c.scope, "core": c.core,
                "status": _promise_status(by_commitment.get(c.id, [])),
            }
            for c in oath.commitments
        ],
        "pages": pages,
        "coverage": cov,
        "degradations": run.degradations,
        "picture_plan": run.picture_plan,
        "ignored_drawing_text": ignored,
        "budget": {
            "usd_estimate": run.meter.cost_usd(st.prices), "estimate": True, "seconds": round(_now() - run.t0, 1),
            "tokens_in": totals["tokens_in"], "tokens_out": totals["tokens_out"], "images": totals["images"],
            "calls": totals["calls"], "by_model": totals["by_model"], "fallbacks": list(run.meter.fallbacks),
            "first_page_s": next((e["t"] for e in run.bus.all() if e["type"] == "scene.accepted"), None),
        },
        "prompt_version": prompts.VERSION,
        "models": {"writer": st.models.writer, "judge": st.models.judge, "vision": st.models.vision, "routes": dict(st.models.routes), "picture_text_judge": st.models.vision_judge},
        "trace_id": run.trace_id,
        "generated_at": ledger.now_ist().isoformat(timespec="seconds"),
    }  # fmt: skip


def _promise_status(vs: list[Verdict]) -> str:
    """kept | broken | not_checked, from the latest verdict of each place the promise applies."""
    live = [v for v in vs if v.status != "skipped"]
    if not live:
        return "not_checked"
    return "kept" if all(v.ok for v in live) else "broken"


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
    def _go(request: dict) -> dict:  # the request and the result are the span's input and output in neatlogs (a reviewer opens the trace here first)
        run.trace_id = tracing.current_trace_id()
        graph = build_graph(run)
        with metered() as meter:
            run.meter = meter
            run.root_ctx = contextvars.copy_context()  # work that outlives the node that started it (judge calls, pictures) is attached to the workflow, not to that node
            graph.invoke({}, {"recursion_limit": 200})
        r = run.receipt or {}
        return {"outcome": run.outcome, "plain": r.get("plain"), "counts": r.get("counts"), "broken": r.get("broken"), "oath_hash": r.get("oath_hash")}

    try:
        _go({"lesson": run.cfg.lesson_id, "age": run.cfg.age, "arm": run.cfg.arm, "pictures": run.cfg.pictures, "attempts_allowed": get_settings().thresholds.max_repair_attempts})
    except Exception as e:
        run.outcome = run.outcome or "error"
        if isinstance(e, ClientError):  # a model service failed after its retries (found by drill C3b): the same soft screen as every other outage
            run.emit("error", {"code": "service_unavailable", "message": "Pip is having trouble right now. Please try again in a minute."})
        else:
            run.emit("error", {"code": "internal", "message": "Something went wrong while making the story."})
        run.error = f"{type(e).__name__}: {e}"[:300]
    finally:
        if run.cfg.ledger_name:
            ledger.append(ledger_row(run))
        run.bus.close()
        tracing.flush()
    return run


def picture_pages(policy: str, indices: list[int], importance: dict[int, int] | None = None, budget_usd: float = 0.0,
                  each_usd: float = 0.04) -> set[int]:
    """Which pages get a picture. Pictures dominate the cost of a story (cfo.ai model), so the plan can paint fewer of them.
    "auto": the agent spends its picture budget on the pages that matter most (the planner's importance, earlier page first)."""
    return set(picture_order(policy, indices, importance, budget_usd, each_usd))


def picture_order(policy: str, indices: list[int], importance: dict[int, int] | None = None, budget_usd: float = 0.0,
                  each_usd: float = 0.04) -> list[int]:
    """The pages to paint, most important first (the order the agent paints them in)."""
    if policy == "none":
        return []
    if policy == "half":
        return [i for i in indices if i % 2 == 1]
    if policy == "auto":
        n = min(len(indices), max(1, int(budget_usd / each_usd + 1e-9))) if indices else 0
        imp = importance or {}
        return sorted(sorted(indices, key=lambda i: (-imp.get(i, 1), i))[:n], key=lambda i: (-imp.get(i, 1), i))
    return list(indices)


def export_story(run: Run, s: S) -> None:
    """Leave a story package next to the media (run_dir/story.json and drawing) so a video can be made from it."""
    d = run.cfg.run_dir
    if not d or run.forgotten:
        return
    d.mkdir(parents=True, exist_ok=True)
    ext = "png" if "png" in (run.drawing.mime or "") else "jpg"
    (d / f"drawing.{ext}").write_bytes(run.drawing.data)
    story = {"story_id": run.story_id, "fixture": run.cfg.fixture, "lesson": run.cfg.lesson_id, "age": run.cfg.age,
             "drawing": f"drawing.{ext}", "card": s["card"].model_dump(), "pages": [p.model_dump() for p in s["pages"]],
             "media": {k: Path(v).relative_to(d).as_posix() for k, v in run.media_paths.items() if v},
             "quiz": run.quiz.model_dump() if run.quiz else None,
             "receipt": run.receipt, "outcome": run.outcome}  # fmt: skip
    (d / "story.json").write_text(json.dumps(story, indent=1, ensure_ascii=False, default=str), encoding="utf-8")


def ledger_row(run: Run) -> dict:
    r = run.receipt or {}
    fails = [
        [v.commitment, v.scope, v.attempt, v.status]
        for v in run.verdicts
        if v.status in ("violation", "critical", "verification_error") or v.judge_status == "verification_error"
    ]
    first_pass = sorted(
        {v.commitment for v in run.verdicts if v.attempt == 0 and v.status in ("violation", "critical")}
    )
    judged = [v for v in run.verdicts if v.verdict_by in ("judge", "both")]
    return {
        "name": run.cfg.ledger_name, "story_id": run.story_id, "fixture": run.cfg.fixture, "lesson": run.cfg.lesson_id,
        "arm": run.cfg.arm, "seed": run.cfg.seed, "age": run.cfg.age, "outcome": run.outcome, "trace_id": run.trace_id,
        "oath_hash": r.get("oath_hash"), "counts": r.get("counts"), "broken": r.get("broken"),
        "first_pass_failed": first_pass, "non_pass_verdicts": fails, "judged": len(judged),
        "judge_errors": sum(1 for v in judged if v.judge_status == "verification_error"),
        "shipped": run.shipped, "degradations": run.degradations, "budget": r.get("budget"),
        "prompt_version": prompts.VERSION, "error": run.error or None, "routes": dict(get_settings().models.routes), "experiment": os.environ.get("STORYBOUND_EXPERIMENT") or None, "chaos": chaos.active() or None, "max_repairs": get_settings().thresholds.max_repair_attempts, "judge_ensemble": get_settings().models.judge_ensemble or None, "hedge_s": get_settings().hedge_after_s, "pictures": run.cfg.pictures, "picture_plan": run.picture_plan, "split": ledger.split_of(run.cfg.fixture),
        "quiz": {**run.quiz_stats, "repairs": sum(1 for r in run.repairs if r.get("stage") == "quiz"), "shown": len(run.quiz.items) if run.quiz else 0},
    }  # fmt: skip
