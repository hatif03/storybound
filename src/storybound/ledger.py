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
