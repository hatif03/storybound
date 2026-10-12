"""Run the B0 (observe-only) vs B1 (gate and repair) comparison over fixtures x lessons x seeds.

  python scripts/sweep.py --name sweep-1 --arms B0,B1 --fixtures benign/bunny-bow-carrot,tier-b-text/fish-kill-fish-caption \
      --lessons sharing,honesty --k 2 --workers 4

Same drawings, same lessons, same seeds, same oath machinery in both arms; only whether verification may change the
outcome differs. Pictures and narration are off. One ledger row per run in evidence/ledger.jsonl; the sweep is resumable
(a finished job with the same name/arm/fixture/lesson/seed is skipped).
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import contextvars
import sys
import threading
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from storybound import ledger, media, tracing  # noqa: E402

tracing.init()

from storybound.events import EventLog  # noqa: E402
from storybound.pipeline import Run, RunConfig, execute  # noqa: E402

FIX = ROOT / "assets" / "test-drawings"
_print = threading.Lock()


def fixture_path(fid: str) -> Path:
    for ext in ("", ".png", ".jpg"):
        if (FIX / (fid + ext)).is_file():
            return FIX / (fid + ext)
    sys.exit(f"unknown fixture {fid}")


def audit_story(run) -> dict:
    """An independent audit of the finished story: every scene promise judged on every page by the full judge, whatever gate the run used.
    Tells how many promise breaks a story still carries when it ships (the measure that lets a judge-less run be compared with a judged one)."""
    from storybound.oath.engine import Engine

    eng = Engine(oath=run.engine.oath, ctx=run.ctx, rates={"quality": 1.0, "image": 0.0}, judge_enabled=True)
    by: dict[str, int] = {}
    for page in run.ctx.pages:
        for v in eng.verify_scene(page, 0):
            if v.status in ("violation", "critical"):
                by[v.commitment] = by.get(v.commitment, 0) + 1
    return {"residual_page_breaks": sum(by.values()), "residual_by_promise": by}


def one(name: str, arm: str, fid: str, lesson: str, seed: str, age: int = 6, no_judge: bool = False, media_on: bool = False, audit: bool = False) -> str:
    d = media.prepare(fixture_path(fid).read_bytes())
    cfg = RunConfig(lesson_id=lesson, age=age, arm=arm, seed=seed, media=media_on, fixture=fid, ledger_name=name, judge_enabled=not no_judge, pictures="auto")
    run = Run(cfg=cfg, drawing=d, bus=EventLog(), story_id=uuid.uuid4().hex[:12])
    t = time.time()
    execute(run)
    c = (run.receipt or {}).get("counts", {})
    if audit and run.ctx.pages:
        resid = audit_story(run)
        ledger.append({"name": name + "-audit", "kind": "audit", "audited": name, "story_id": run.story_id, "fixture": fid, "lesson": lesson, "pages": len(run.ctx.pages), **resid})
    msg = f"{arm} {fid.split('/')[-1][:28]:28} {lesson:9} seed={seed} -> {run.outcome:19} shipped={len(run.shipped)} repairs={c.get('repairs', '-')} {time.time() - t:5.0f}s"
    with _print:
        print(msg, flush=True)
    return msg


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--arms", default="B0,B1")
    ap.add_argument("--fixtures", required=True)
    ap.add_argument("--lessons", default="sharing")
    ap.add_argument("--k", type=int, default=2)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--age", type=int, default=6, help="the reader's age, 4 to 8")
    ap.add_argument("--audit", action="store_true", help="after each story, judge every page on every scene promise (residual breaks)")
    ap.add_argument("--no-judge", action="store_true", help="deterministic checks only (experiment X4)")
    ap.add_argument("--media", action="store_true", help="paint and narrate too (drills that need the picture and voice services)")
    a = ap.parse_args()
    done = {
        (r.get("arm"), r.get("fixture"), r.get("lesson"), str(r.get("seed")))
        for r in ledger.read()
        if r.get("name") == a.name and not r.get("error")
    }
    jobs = [
        (arm, f, les, str(k))
        for k in range(1, a.k + 1)
        for f in a.fixtures.split(",")
        for les in a.lessons.split(",")
        for arm in a.arms.split(",")
        if (arm, f, les, str(k)) not in done
    ]
    print(f"{len(jobs)} runs to do ({len(done)} already in the ledger)", flush=True)
    with cf.ThreadPoolExecutor(max_workers=a.workers) as pool:
        futs = [pool.submit(contextvars.copy_context().run, one, a.name, *j, a.age, a.no_judge, a.media, a.audit) for j in jobs]
        for f in futs:
            try:
                f.result()
            except Exception as e:
                print("job failed:", type(e).__name__, str(e)[:120], flush=True)
    tracing.flush()


if __name__ == "__main__":
    main()
