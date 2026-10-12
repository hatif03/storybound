"""Compare the experiments and drills in the ledger against the baseline.

  python scripts/compare_experiments.py [--md evidence/experiments/<file>.md]

One line per experiment name (rows with the same `name`): stories, outcomes, first-pass breaks, shipped breaks, repairs, seconds, estimated cost,
degradations, and which model did the work. Baseline for X* is `holdout-routes-default` (the default routing on the same drawings), for C* none (a
drill is read against what it should have done: ship, or stop kindly).
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from storybound import ledger  # noqa: E402

BASE = "holdout-routes-default"
ORDER = ["X", "C"]


def stats(rows: list[dict]) -> dict:
    ok = [r for r in rows if not r.get("error")]
    n = len(rows)
    out = collections.Counter(r.get("outcome") or ("error" if r.get("error") else "?") for r in rows)
    models: dict[str, list[int]] = {}
    for r in ok:
        for m, v in ((r.get("budget") or {}).get("by_model") or {}).items():
            a = models.setdefault(m, [0, 0, 0])
            a[0] += v.get("in", 0)
            a[1] += v.get("out", 0)
            a[2] += v.get("calls", 0)
    deg = collections.Counter(d.get("what") for r in rows for d in (r.get("degradations") or []))
    return {
        "n": n,
        "outcomes": dict(out),
        "errors": n - len(ok),
        "first_pass_broke": sum(1 for r in ok if r.get("first_pass_failed")),
        "shipped_break": sum(1 for r in ok if r.get("shipped")),
        "repairs": round(sum((r.get("counts") or {}).get("repairs", 0) for r in ok) / max(1, len(ok)), 2),
        "seconds": round(sum((r.get("budget") or {}).get("seconds", 0) for r in ok) / max(1, len(ok))),
        "p_max_seconds": round(max(((r.get("budget") or {}).get("seconds", 0) for r in ok), default=0)),
        "usd_est": round(sum((r.get("budget") or {}).get("usd_estimate", 0) for r in ok) / max(1, len(ok)), 4),
        "quiz_shown": sum((r.get("quiz") or {}).get("shown", 0) for r in ok),
        "degradations": dict(deg),
        "models": {m: tuple(v) for m, v in models.items()},
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", default="")
    a = ap.parse_args()
    rows = ledger.read()
    names = [BASE] + sorted({r["name"] for r in rows if str(r.get("name", "")).startswith(("X", "C")) and r.get("arm") == "B1"})
    table = {n: stats([r for r in rows if r.get("name") == n and r.get("arm") == "B1"]) for n in names}
    lines = ["| Run | Stories | Outcomes | Errors | First pass broke | Shipped a break | Repairs / story | Seconds (mean, max) | Est. USD / story | Quiz shown | Degradations |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for n, s in table.items():
        if not s["n"]:
            continue
        lines.append(f"| {n} | {s['n']} | {s['outcomes']} | {s['errors']} | {s['first_pass_broke']} | {s['shipped_break']} | {s['repairs']} | {s['seconds']}, {s['p_max_seconds']} | {s['usd_est']} | {s['quiz_shown']} | {s['degradations']} |")
    text = "\n".join(lines)
    print(text)
    if a.md:
        Path(a.md).parent.mkdir(parents=True, exist_ok=True)
        Path(a.md).write_text(text + "\n\n```json\n" + json.dumps(table, indent=1) + "\n```\n", encoding="utf-8")


if __name__ == "__main__":
    main()
