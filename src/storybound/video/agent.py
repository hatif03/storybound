"""The video agent: plan -> narrate -> compose -> check -> render -> verify -> repair -> receipt, under one neatlogs trace.

A workflow with one agentic loop (verify, then repair the failing scene, at most MAX_REPAIRS rounds). The planner sees
claim labels only, never values, and every number on screen is resolved from an evidence file at render time.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

from .. import ledger, tracing
from ..agents.common import ask_json
from ..clients import tts
from ..clients.usage import metered
from ..config import get_settings
from . import claims, compose, render, verify
from .spec import Scene, Spec

MAX_REPAIRS = 2
NARRATION_STYLE = "Speak clearly in a warm, upbeat, natural pace, like a friendly presenter."

PLAN_SYSTEM = (
    "You plan a short explainer video as JSON. You may NOT write any digit (0-9) anywhere. Numbers reach the screen only "
    "through claims: a claim block {type:'claim', claim:<id>}, a bars block whose items are {label, claim, tone} with "
    "tone 'good' or 'bad', or a {claim_id} placeholder inside narration. Block types: title, text, claim, bars, list. "
    "Write warm, plain narration for a general audience, one or two short sentences per scene, about one hundred words in total. Do not claim more than the claims show. Give each scene a \"mood\" for Pip the owl mascot, one of: happy-flap, wink, dizzy-confused, cool-sunglasses, heart-eyes, party-cupcake, shy-giggle (dizzy-confused for a problem, cool-sunglasses or wink for the fix, heart-eyes or party-cupcake for good results). Use only the claim ids given. "
    "Answer with JSON only: {\"scenes\": [{\"id\", \"narration\", \"blocks\": [...], \"covers\": [], \"mood\": \"happy-flap\"}]}. Do not include any timing fields."
)
REPAIR_SYSTEM = (
    "You repair ONE scene of a video spec. Fix only the stated failure, change as little as possible. Never write a digit "
    "(0-9): numbers come from claims ({claim_id} placeholders in narration, claim and bars blocks). Keep block types from "
    "title, text, claim, bars, list. Keep text short enough to fit a 1920x1080 frame. Answer with the repaired scene as "
    "JSON only: {\"id\", \"narration\", \"blocks\", \"covers\"}."
)


@tracing.span(kind="AGENT", name="node.plan")
def plan(brief: str, catalog: list[dict], title: str) -> Spec:
    lines = "\n".join(f"- {c['id']}: {c['label']}" for c in catalog)
    r = ask_json("video_planner", PLAN_SYSTEM, f"Brief: {brief}\n\nClaims you can use (ids and meaning only):\n{lines}",
                 temperature=0.5, max_tokens=4096)  # fmt: skip
    scenes = [{k: v for k, v in sc.items() if k != "min_seconds"} for sc in r.value["scenes"]]  # timing is ours, not the planner's
    return Spec.model_validate({"title": title, "claims": catalog, "scenes": scenes})


@tracing.span(kind="AGENT", name="node.repair")
def repair(spec: Spec, failures: list[dict]) -> Spec:
    """Rewrite each failing scene once, with only that scene and its failures as context."""
    by_scene: dict[str, list[dict]] = {}
    for f in failures:
        if f.get("scene") and any(s.id == f["scene"] for s in spec.scenes):
            by_scene.setdefault(f["scene"], []).append(f)
    scenes = list(spec.scenes)
    for i, sc in enumerate(scenes):
        if sc.id not in by_scene:
            continue
        info = "; ".join(f"{f['commitment']}: expected {f['expected']}, got {f['actual']}" for f in by_scene[sc.id])
        ids = ", ".join(c.id for c in spec.claims)
        r = ask_json(f"video_repair.{sc.id}", REPAIR_SYSTEM,
                     f"Scene:\n{sc.model_dump_json()}\n\nFailure: {info}\nClaim ids: {ids}", temperature=0.3, max_tokens=2048)  # fmt: skip
        try:
            scenes[i] = Scene.model_validate({**r.value, "id": sc.id})
        except Exception:
            pass  # an unusable rewrite leaves the scene as it was; the next verify reports it again
    return spec.model_copy(update={"scenes": scenes})


def _probe(mp3: Path) -> float:
    p = subprocess.run([shutil.which("ffprobe") or "ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(mp3)], capture_output=True, text=True)  # fmt: skip
    return float(p.stdout.strip())


@tracing.span(kind="TOOL", name="narrate_scenes")
def narrate_all(texts: dict[str, str], out: Path, style: str = NARRATION_STYLE) -> dict[str, tuple[Path, float]]:
    """One narration clip per scene, loudness-normalised, cached by text so a repair only re-voices what changed."""
    cache = out / "audio-cache"
    cache.mkdir(parents=True, exist_ok=True)
    got = {}
    for sid, text in texts.items():
        h = hashlib.sha256((style + text).encode()).hexdigest()[:16]
        f = cache / f"{h}.mp3"
        if not f.exists():
            raw = cache / f"{h}.raw.mp3"
            raw.write_bytes(tts.narrate(text, style=style).value)
            subprocess.run([shutil.which("ffmpeg") or "ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-af",
                            "loudnorm=I=-16:TP=-1.5:LRA=11", str(f)], check=True)  # fmt: skip
            raw.unlink()
        got[sid] = (f, _probe(f))
    return got


def _scene_at(timeline: dict, seconds: float) -> str | None:
    for s in timeline["scenes"]:
        if s["start"] <= seconds < s["start"] + s["dur"]:
            return s["id"]
    return None


def _layout_failures(chk: dict, timeline: dict) -> list[dict]:
    """Map HyperFrames problems to scenes by the timestamps they mention, so repair can target the scene."""
    fails = []
    for prob in chk["problems"]:
        times = [float(x) for x in re.findall(r"(?<![\w.])(\d+(?:\.\d+)?)(?=[,s\s)])", prob.split("t=", 1)[-1])] if "t=" in prob else []
        sid = _scene_at(timeline, times[0]) if times else None
        fails.append({"commitment": "renders_clean", "status": "violation", "expected": "HyperFrames check passes",
                      "actual": prob[:200], "scene": sid})  # fmt: skip
    return fails


def make(spec: Spec | None, *, brief: str = "", catalog: list[dict] | None = None, title: str = "video",
         out: Path, max_repairs: int = MAX_REPAIRS, name: str = "") -> dict:
    """Run the agent and return the receipt. Never raises: a failure is an outcome in the receipt."""
    out.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("NEATLOGS_WORKFLOW", "make-video")
    receipt: dict = {"name": name or title, "attempts": [], "repairs": []}
    t0 = time.time()

    @tracing.span(kind="WORKFLOW", name="make-video")
    def _go() -> None:
        nonlocal spec
        receipt["trace_id"] = tracing.current_trace_id()
        with metered() as meter:
            if spec is None:
                spec = plan(brief, catalog or [], title)
            (out / "spec.json").write_text(spec.model_dump_json(indent=1), encoding="utf-8")
            for attempt in range(max_repairs + 1):
                resolved = claims.resolve(spec)
                audio = narrate_all(compose.spoken_text(spec, resolved), out, spec.narration_style or NARRATION_STYLE)
                timeline = compose.build(spec, resolved, audio, out / "project")
                chk = render.check(out / "project")
                verdicts = [*verify.static(spec, resolved, timeline["total"]), verify.renders_clean(chk)]
                for v in verdicts:
                    with tracing.guardrail_span(v["commitment"], scope=v.get("scene") or "video", input_text=v["actual"]) as sp:
                        tracing.record(sp, {**v, "attempt": attempt, "verdict_by": "deterministic"})
                receipt["attempts"].append({"attempt": attempt, "verdicts": verdicts, "total_s": timeline["total"]})
                bad = [v for v in verdicts if v["status"] != "pass"]
                if not bad or attempt == max_repairs:
                    break
                bad = [v for v in bad if v["commitment"] != "renders_clean"] + _layout_failures(chk, timeline) if not chk["passed"] else bad
                if not any(v.get("scene") for v in bad):  # nothing a scene rewrite can fix: stop and ship with notes
                    receipt["repairs"].append({"attempt": attempt + 1, "stopped": "failures not tied to a scene"})
                    break
                before = spec.digest()
                spec = repair(spec, bad)
                receipt["repairs"].append({"attempt": attempt + 1, "failed": sorted({v["commitment"] for v in bad}),
                                           "scenes": sorted({v["scene"] for v in bad if v.get("scene")}), "changed": spec.digest() != before})  # fmt: skip
                (out / "spec.json").write_text(spec.model_dump_json(indent=1), encoding="utf-8")
            mp4 = out / "video.mp4"
            r = render.render(out / "project", mp4)
            receipt["render"] = r
            final = receipt["attempts"][-1]["verdicts"]
            if r["ok"]:
                av = verify.audio_ok(mp4, timeline)
                final = [*final, av]
                receipt["attempts"][-1]["verdicts"] = final
                with tracing.guardrail_span("audio_ok", scope="video", input_text=av["actual"]) as sp:
                    tracing.record(sp, {**av, "attempt": attempt, "verdict_by": "deterministic"})
                receipt["video"] = {"file": mp4.name, "sha256": hashlib.sha256(mp4.read_bytes()).hexdigest(),
                                    "seconds": timeline["total"], "bytes": mp4.stat().st_size}  # fmt: skip
            broken = [v for v in final if v["status"] != "pass"]
            receipt["outcome"] = "shipped" if r["ok"] and not broken else ("shipped_with_notes" if r["ok"] else "error")
            receipt["broken"] = [{k: v[k] for k in ("commitment", "scene", "actual")} for v in broken]
            receipt["spec_digest"] = spec.digest()
            receipt["claims"] = [{k: c[k] for k in ("id", "label", "display", "sources")} for c in resolved.values()]
            receipt["budget"] = {**meter.totals(), "usd_estimate": meter.cost_usd(get_settings().prices), "estimate": True}

    try:
        _go()
    except Exception as e:
        receipt["outcome"] = receipt.get("outcome") or "error"
        receipt["error"] = f"{type(e).__name__}: {e}"[:300]
    receipt["seconds"] = round(time.time() - t0, 1)
    receipt["hyperframes"] = render.VERSION
    tracing.flush()
    (out / "receipt.json").write_text(json.dumps(receipt, indent=1, default=str), encoding="utf-8")
    if name:
        ledger.append({"name": name, "kind": "video", "outcome": receipt.get("outcome"), "trace_id": receipt.get("trace_id"),
                       "broken": receipt.get("broken"), "repairs": len(receipt["repairs"]), "budget": receipt.get("budget"),
                       "spec_digest": receipt.get("spec_digest"), "video": receipt.get("video"), "error": receipt.get("error")})  # fmt: skip
    return receipt
