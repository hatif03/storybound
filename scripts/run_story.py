"""Run one story from the command line.

  python scripts/run_story.py benign/bunny-bow-carrot --lesson sharing [--arm B1|B0] [--media] [--seed 1] [--name label]

Prints the event stream in short form and the receipt. With --name the run is appended to evidence/ledger.jsonl.
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from storybound import tracing  # noqa: E402

tracing.init()

from storybound import media  # noqa: E402
from storybound.events import EventLog  # noqa: E402
from storybound.pipeline import Run, RunConfig, execute  # noqa: E402

FIXTURES = ROOT / "assets" / "test-drawings"


def find_fixture(fid: str) -> Path:
    for ext in ("", ".png", ".jpg", ".jpeg"):
        p = FIXTURES / (fid + ext)
        if p.is_file():
            return p
    sys.exit(f"unknown fixture {fid}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("fixture")
    ap.add_argument("--lesson", default="sharing")
    ap.add_argument("--arm", default="B1")
    ap.add_argument("--seed", default="1")
    ap.add_argument("--age", type=int, default=6)
    ap.add_argument("--hero")
    ap.add_argument("--media", action="store_true")
    ap.add_argument("--no-judge", action="store_true")
    ap.add_argument("--pictures", default="full", help="full | half | none | auto (the agent chooses the pages)")
    ap.add_argument("--name", help="ledger name; omit for a scratch run")
    ap.add_argument("--out", help="write the receipt and events JSON here")
    a = ap.parse_args()

    path = find_fixture(a.fixture)
    drawing = media.prepare(path.read_bytes())
    sid = uuid.uuid4().hex[:12]
    cfg = RunConfig(
        lesson_id=a.lesson, age=a.age, hero_name=a.hero, arm=a.arm, seed=a.seed, media=a.media,
        run_dir=(ROOT / "runs" / sid) if a.media else None, fixture=a.fixture, ledger_name=a.name,
        judge_enabled=not a.no_judge, pictures=a.pictures,
    )  # fmt: skip
    bus = EventLog()
    run = Run(cfg=cfg, drawing=drawing, bus=bus, story_id=sid)
    t = threading.Thread(target=execute, args=(run,))
    t.start()
    i = 0
    while True:
        evs, done = bus.since(i, 2.0)
        for e in evs:
            i = e["id"] + 1
            d = e["data"]
            if e["type"] == "verdict":
                if d["status"] not in ("pass", "skipped"):
                    print(
                        f"  [{e['t']:6.1f}s] verdict {d['commitment']} {d['scope']} -> {d['status']}: {d['actual'][:100]}"
                    )
            elif e["type"] == "scene.accepted":
                print(f"[{e['t']:6.1f}s] accepted page {d['index']} after {d['attempts_used']} repair(s)")
            else:
                brief = {k: v for k, v in d.items() if k not in ("commitments", "card", "beats", "page", "by_model")}
                print(f"[{e['t']:6.1f}s] {e['type']} {json.dumps(brief, ensure_ascii=False)[:200]}")
        if done:
            break
    t.join()
    if a.out:
        Path(a.out).write_text(
            json.dumps(
                {"receipt": run.receipt, "events": bus.all(), "shipped": run.shipped}, indent=2, ensure_ascii=False
            ),
            encoding="utf-8",
        )
    print("\nOUTCOME:", run.outcome, "| trace", run.trace_id, "| error:", run.error or "none")
    if run.receipt:
        print("RECEIPT:", run.receipt["plain"], "| shipped violations:", len(run.shipped), "| est. $", run.receipt["budget"]["usd_estimate"],
              "|", run.receipt["budget"]["seconds"], "s")  # fmt: skip


if __name__ == "__main__":
    main()
