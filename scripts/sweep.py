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


def one(name: str, arm: str, fid: str, lesson: str, seed: str) -> str:
    d = media.prepare(fixture_path(fid).read_bytes())
    cfg = RunConfig(lesson_id=lesson, arm=arm, seed=seed, media=False, fixture=fid, ledger_name=name)
    run = Run(cfg=cfg, drawing=d, bus=EventLog(), story_id=uuid.uuid4().hex[:12])
    t = time.time()
    execute(run)
    c = (run.receipt or {}).get("counts", {})
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
        futs = [pool.submit(contextvars.copy_context().run, one, a.name, *j) for j in jobs]
        for f in futs:
            try:
                f.result()
            except Exception as e:
                print("job failed:", type(e).__name__, str(e)[:120], flush=True)
    tracing.flush()


if __name__ == "__main__":
    main()
