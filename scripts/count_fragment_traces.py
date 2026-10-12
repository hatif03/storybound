"""Count traces that are not a whole story (one to four spans) in each experiment's time window (HR-016).

  python scripts/count_fragment_traces.py [experiment names]

Needs a neatlogs CLI sign-in (it lasts about 15 minutes). Results are merged into evidence/neatlogs/review-3/fragment_traces_by_experiment.json.
"""

import collections
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from storybound import ledger  # noqa: E402

N = shutil.which("neatlogs") or "neatlogs"
OUTFILE = ROOT / "evidence" / "neatlogs" / "review-3" / "fragment_traces_by_experiment.json"
ENV = {k: v for k, v in os.environ.items() if not k.startswith("NEATLOGS_")}
rows = [r for r in ledger.read() if r.get("kind") != "audit" and r.get("name")]
win = {}
for r in rows:
    t = datetime.fromisoformat(r["ts_utc"])
    n = r["name"]
    lo, hi = win.get(n, (t, t))
    win[n] = (min(lo, t), max(hi, t))
want = sys.argv[1:] or [
    "X6-repairs-4",
    "X2b-writer-claude-sonnet-fixed",
    "A0-baseline-audit",
    "A4-no-judge-audit",
    "A5-repairs-0-audit",
    "C3b-gemini-503-after-fix",
    "C4b-judge-down-failover",
]
out = json.loads(OUTFILE.read_text(encoding="utf-8")) if OUTFILE.exists() else {}
for n in want:
    if n not in win:
        print(n, "is not in the ledger; skipped")
        continue
    lo, hi = win[n]
    # the ledger row is written at the end of a story: a story can start 7 minutes before its row
    a, b = (
        (lo - timedelta(seconds=260)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        (hi + timedelta(seconds=30)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    p = subprocess.run(
        [N, "traces", "list", "--from", a, "--to", b, "--all", "--max-items", "1000"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=ENV,
        timeout=300,
    )
    try:
        t = json.loads(p.stdout)["data"]["traces"]
    except Exception:
        print(n, "list failed", p.stdout[:100])
        continue
    whole = sum(1 for x in t if x["traceName"] == "create-storybook" and x["spansCount"] > 4)
    frag = collections.Counter((x["traceName"], x["spansCount"]) for x in t if x["spansCount"] <= 4)
    out[n] = {
        "window": [a, b],
        "traces": len(t),
        "whole_stories": whole,
        "stories_in_ledger": sum(1 for r in rows if r["name"] == n),
        "fragments": sum(frag.values()),
        "fragment_kinds": [[list(k), v] for k, v in frag.most_common(6)],
    }
    print(
        n,
        out[n]["traces"],
        "traces,",
        whole,
        "whole,",
        out[n]["fragments"],
        "fragments",
        frag.most_common(3),
        flush=True,
    )
OUTFILE.write_text(json.dumps(out, indent=1), encoding="utf-8")
