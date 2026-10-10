"""HyperFrames as two tools: `check` (lint, runtime, layout, motion, contrast) and `render`. Pinned version, telemetry off."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from pathlib import Path

VERSION = "0.8.145"
_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def _run(args: list[str], cwd: Path, timeout: int) -> tuple[int, str]:
    env = {**os.environ, "HYPERFRAMES_SKIP_SKILLS": "1", "DO_NOT_TRACK": "1", "NO_COLOR": "1"}
    npx = shutil.which("npx") or "npx"
    p = subprocess.run(
        [npx, "--yes", f"hyperframes@{VERSION}", *args], cwd=cwd, env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=timeout,
    )  # fmt: skip
    return p.returncode, _ANSI.sub("", p.stdout + p.stderr)


def check(project: Path) -> dict:
    """Returns {passed, problems: [str]}. A lint error means the browser checks did not run: that is a failure too."""
    code, out = _run(["check"], project, 300)
    problems = [ln.strip() for ln in out.splitlines() if ln.strip().startswith("✗") or "Browser session never ran" in ln]
    passed = "Check passed" in out and not problems
    return {"passed": passed, "problems": problems, "raw_tail": out[-1500:], "exit": code}


def render(project: Path, mp4: Path) -> dict:
    t0 = time.time()
    code, out = _run(["render", "-o", "video.mp4"], project, 900)  # relative: the CLI mangles absolute paths on Windows
    made = project / "video.mp4"
    if code != 0 or not made.exists():
        return {"ok": False, "seconds": round(time.time() - t0, 1), "raw_tail": out[-1500:]}
    shutil.move(str(made), str(mp4))
    return {"ok": True, "seconds": round(time.time() - t0, 1)}
