"""The architecture and configuration experiments and the failure drills of 12 Oct, run one after another, each a tagged sweep in the ledger.

  python scripts/run_experiments.py [--only X1,C4] [--list]

Experiments (X*) run the held-out drawings (5 drawings x sharing and honesty = 10 stories, gated arm) so each can be compared with the baseline
`holdout-routes-default`; drills (C*) inject a failure (src/storybound/chaos.py) into 5 stories and watch the agent's own recovery. Every run
is tagged in neatlogs (`experiment` or `chaos`) so the traces can be told from product runs, and every row in `evidence/ledger.jsonl` carries
the configuration (`experiment`, `chaos`, `routes`, `max_repairs`, `judge_ensemble`, `hedge_s`). Results are read with `scripts/compare_experiments.py`.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = str(ROOT / ".venv" / "Scripts" / "python.exe")
HOLDOUT = "benign/chameleon-hummingbird,benign/schoolroom-1909,edge/sailing-ship-pencil-low-contrast,edge/baba-yaga-1916-spooky-witch,edge/pii-name-written-on-drawing"
DRILL = "benign/bunny-bow-carrot,benign/chameleon-hummingbird,benign/schoolroom-1909,edge/baba-yaga-1916-spooky-witch,benign/christmas-tree-digital"
DEFAULT_ROUTES = "story_planner=nova-2-lite,quiz_maker=claude-haiku,quiz_repair=claude-haiku"

# name: (environment, sweep arguments)
EXPERIMENTS = {
    "X1-writer-gemini-pro": ({"STORYBOUND_ROUTES": DEFAULT_ROUTES + ",scene_writer=gemini-3.1-pro-preview,scene_repair=gemini-3.1-pro-preview"}, ["--fixtures", HOLDOUT, "--lessons", "sharing,honesty"]),
    "X2-writer-claude-sonnet": ({"STORYBOUND_ROUTES": DEFAULT_ROUTES + ",scene_writer=claude-sonnet-4.6,scene_repair=claude-sonnet-4.6"}, ["--fixtures", HOLDOUT, "--lessons", "sharing,honesty"]),
    "X3-judge-ensemble": ({"STORYBOUND_JUDGE_ENSEMBLE": "claude-sonnet-4.6"}, ["--fixtures", HOLDOUT, "--lessons", "sharing,honesty"]),
    "X4-no-judge": ({}, ["--fixtures", HOLDOUT, "--lessons", "sharing,honesty", "--no-judge"]),
    "X5-repairs-0": ({"STORYBOUND_MAX_REPAIRS": "0"}, ["--fixtures", HOLDOUT, "--lessons", "sharing,honesty"]),
    "X6-repairs-4": ({"STORYBOUND_MAX_REPAIRS": "4"}, ["--fixtures", HOLDOUT, "--lessons", "sharing,honesty"]),
    # second round (12 Oct): the Sonnet writer again after the parser fix, and the audit pass that measures the breaks a story still carries when it ships
    "X2b-writer-claude-sonnet-fixed": ({"STORYBOUND_ROUTES": DEFAULT_ROUTES + ",scene_writer=claude-sonnet-4.6,scene_repair=claude-sonnet-4.6"}, ["--fixtures", HOLDOUT, "--lessons", "sharing,honesty"]),
    "A0-baseline-audit": ({}, ["--fixtures", HOLDOUT, "--lessons", "sharing,honesty", "--audit"]),
    "A4-no-judge-audit": ({}, ["--fixtures", HOLDOUT, "--lessons", "sharing,honesty", "--no-judge", "--audit"]),
    "A5-repairs-0-audit": ({"STORYBOUND_MAX_REPAIRS": "0"}, ["--fixtures", HOLDOUT, "--lessons", "sharing,honesty", "--audit"]),
    "C1-stall-hedge-on": ({"STORYBOUND_CHAOS": "gemini:stall:100:0.15"}, ["--fixtures", DRILL, "--lessons", "sharing"]),
    "C2-stall-hedge-off": ({"STORYBOUND_CHAOS": "gemini:stall:100:0.15", "STORYBOUND_HEDGE_S": "0"}, ["--fixtures", DRILL, "--lessons", "sharing"]),
    "C3-gemini-503": ({"STORYBOUND_CHAOS": "gemini:error:503:0.4"}, ["--fixtures", DRILL, "--lessons", "sharing"]),
    "C4-judge-down": ({"STORYBOUND_CHAOS": "k2:error:503:1"}, ["--fixtures", DRILL, "--lessons", "sharing"]),
    # after the fixes made from drills C3 and C4 (HR-015): the same failures again, and both judges down
    "C3b-gemini-503-after-fix": ({"STORYBOUND_CHAOS": "gemini:error:503:0.4"}, ["--fixtures", DRILL, "--lessons", "sharing"]),
    "C4b-judge-down-failover": ({"STORYBOUND_CHAOS": "k2:error:503:1"}, ["--fixtures", DRILL, "--lessons", "sharing"]),
    "C7-both-judges-down": ({"STORYBOUND_CHAOS": "k2:error:503:1,gateway:error:503:1"}, ["--fixtures", DRILL, "--lessons", "sharing"]),
    "C5-gateway-down": ({"STORYBOUND_CHAOS": "gateway:error:503:1"}, ["--fixtures", DRILL, "--lessons", "sharing"]),
    "C6-image-429": ({"STORYBOUND_CHAOS": "image:error:429:0.8"}, ["--fixtures", "benign/bunny-bow-carrot,benign/chameleon-hummingbird,benign/schoolroom-1909", "--lessons", "sharing", "--media"]),
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--workers", default="3")
    a = ap.parse_args()
    if a.list:
        for k, (e, _args) in EXPERIMENTS.items():
            print(k, e)
        return
    want = [w for w in a.only.split(",") if w] or list(EXPERIMENTS)
    for name in EXPERIMENTS:
        if not any(name.startswith(w) for w in want):
            continue
        env_extra, args = EXPERIMENTS[name]
        env = {**os.environ, "STORYBOUND_EXPERIMENT": name, "STORYBOUND_TAGS": "chaos" if name.startswith("C") else "experiment", **env_extra}
        out = ROOT / "runs" / f"exp-{name}.out"
        t0 = time.time()
        with out.open("w", encoding="utf-8") as f:
            subprocess.run([PY, str(ROOT / "scripts" / "sweep.py"), "--name", name, "--arms", "B1", "--k", "1", "--workers", a.workers, *args], env=env, stdout=f, stderr=subprocess.STDOUT, cwd=ROOT)
        print(f"{name} done in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    sys.exit(main())
