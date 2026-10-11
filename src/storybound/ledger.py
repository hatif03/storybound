"""Append-only evidence ledger: one JSON line per named run (evidence/ledger.jsonl)."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .config import ROOT

LEDGER = ROOT / "evidence" / "ledger.jsonl"
IST = timezone(timedelta(hours=5, minutes=30))


# Which drawings were used while prompts and checks were being tuned (sweeps 1 to 7) and which were kept back. Every number computed on a
# "tuning" drawing was seen while changing the system; only "holdout" numbers are on data the changes never looked at (declared 11 Oct).
HOLDOUT = {
    "benign/chameleon-hummingbird", "benign/schoolroom-1909", "edge/sailing-ship-pencil-low-contrast",
    "edge/baba-yaga-1916-spooky-witch", "edge/pii-name-written-on-drawing",
}  # fmt: skip
TUNING = {
    "benign/bunny-bow-carrot", "benign/christmas-tree-digital", "benign/rhinoceros-crayon", "benign/van-crayon", "benign/rabbit-tree-rainbow",
    "tier-b-text/fish-kill-fish-caption", "tier-b-text/injection-ignore-instructions", "edge/copyrighted-character-mickey-1928",
}  # fmt: skip


def split_of(fixture: str | None) -> str | None:
    return "holdout" if fixture in HOLDOUT else "tuning" if fixture in TUNING else None


def now_ist() -> datetime:
    return datetime.now(IST)


def stamp(what: str) -> str:
    """YYYYMMDD-HHMM-IST-<what>, the screenshot/export naming rule from CLAUDE.md."""
    return f"{now_ist():%Y%m%d-%H%M}-IST-{what}"


def git_sha() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:
        return ""


def append(row: dict[str, Any], path: Path = LEDGER) -> dict[str, Any]:
    """Add one row. Timestamps and sha are filled in; secrets must never be passed in."""
    full = {
        "ts_ist": now_ist().isoformat(timespec="seconds"),
        "ts_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "git_sha": git_sha(),
        **row,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(full, ensure_ascii=False, default=str) + "\n")
    return full


def read(path: Path = LEDGER) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
