"""Pre-submission linter: checks the rules the hackathon states, against the repo as it is.

  python scripts/lint_evidence.py [--strict]

Checks: commits inside the window, Entire checkpoint trailers, secrets (values from .env) absent from tracked files,
ledger present with traces, hardening records complete, posts file, demo video length, public posts, cfo.ai link.
Exit code 1 if any FAIL (and, with --strict, any WARN).
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from storybound import ledger  # noqa: E402

IST = timezone(timedelta(hours=5, minutes=30))
WINDOW_START = datetime(2026, 10, 10, 12, 30, tzinfo=IST)  # kickoff
WINDOW_END = datetime(2026, 10, 12, 23, 55, tzinfo=IST)
results: list[tuple[str, str, str]] = []


def add(status: str, name: str, detail: str = "") -> None:
    results.append((status, name, detail))


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8").stdout


def check_commits() -> None:
    rows = [line.split("|", 2) for line in git("log", "--format=%H|%aI|%s").splitlines() if line]
    if not rows:
        return add("FAIL", "commits", "no commits")
    outside = []
    for sha, iso, subj in rows:
        t = datetime.fromisoformat(iso)
        if not (WINDOW_START <= t <= WINDOW_END):
            outside.append(f"{sha[:7]} {iso} {subj[:40]}")
    add(
        "PASS" if not outside else "FAIL",
        "commits inside the window",
        f"{len(rows)} commits; outside: {outside or 'none'}",
    )


def check_checkpoints() -> None:
    log = git("log", "--format=%H|%(trailers:key=Entire-Checkpoint,valueonly)")
    total = with_cp = 0
    for line in log.splitlines():
        if "|" in line:
            total += 1
            with_cp += bool(line.split("|", 1)[1].strip())
    if with_cp == 0:
        add("WARN", "Entire checkpoints linked to commits", f"0 of {total} commits carry an Entire-Checkpoint trailer")
    else:
        add("PASS", "Entire checkpoints linked to commits", f"{with_cp} of {total} commits")
    graph = list((ROOT / "evidence" / "entire").glob("*graph*"))
    add("PASS" if graph else "WARN", "entire graph output saved", f"{len(graph)} file(s)")


def check_secrets() -> None:
    env = ROOT / ".env"
    if not env.exists():
        return add("WARN", "secret scan", ".env not found, cannot compare values")
    secrets = []
    for line in env.read_text(encoding="utf-8").splitlines():
        if "=" not in line or line.lstrip().startswith("#"):
            continue
        name, val = line.split("=", 1)
        val = val.strip().strip('"').strip("'")
        if re.search(r"KEY|SECRET|TOKEN|PASSWORD", name, re.I) and len(val) >= 12:
            secrets.append(val)
    files = [f for f in git("ls-files").splitlines() if not f.startswith(("assets/", "web/public/"))]
    hits = []
    for f in files:
        p = ROOT / f
        if not p.is_file() or p.stat().st_size > 5_000_000:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        if any(s in text for s in secrets):
            hits.append(f)
    key_like = re.compile(r"(AKIA[0-9A-Z]{16}|ya29\.[0-9A-Za-z_-]{20,}|sk-[A-Za-z0-9]{20,}|IFM-[A-Za-z0-9]{12,})")
    for f in files:
        p = ROOT / f
        if (
            p.is_file()
            and p.stat().st_size < 2_000_000
            and p.suffix in {".md", ".py", ".json", ".jsonl", ".txt", ".ts", ".tsx", ".yml", ".toml"}
        ):
            try:
                if key_like.search(p.read_text(encoding="utf-8")):
                    hits.append(f + " (key-shaped)")
            except Exception:
                pass
    add(
        "PASS" if not hits else "FAIL",
        "no secrets in tracked files",
        f"checked {len(files)} files; hits: {hits or 'none'}",
    )


def check_ledger() -> None:
    rows = ledger.read()
    runs = [r for r in rows if r.get("arm")]
    add("PASS" if runs else "WARN", "ledger has story runs", f"{len(runs)} runs, {len(rows)} rows")
    no_trace = [r for r in runs if not r.get("trace_id")]
    add("PASS" if not no_trace else "FAIL", "every run has a neatlogs trace id", f"{len(no_trace)} without")
    for need in ("B0", "B1"):
        n = sum(1 for r in runs if r["arm"] == need)
        add("PASS" if n else "WARN", f"arm {need} measured", f"{n} runs")


def check_hardening() -> None:
    recs = sorted((ROOT / "evidence" / "hardening").glob("HR-*.md"))
    add("PASS" if recs else "WARN", "hardening records", f"{len(recs)} record(s)")
    for r in recs:
        text = r.read_text(encoding="utf-8")
        missing = [h for h in ("Trigger", "Diagnosis", "Change", "Before", "After") if h.lower() not in text.lower()]
        add("PASS" if not missing else "FAIL", f"{r.name} complete", f"missing: {missing or 'none'}")


def check_posts_video_cfo() -> None:
    posts = (
        (ROOT / "evidence" / "posts.md").read_text(encoding="utf-8")
        if (ROOT / "evidence" / "posts.md").exists()
        else ""
    )
    n = len(re.findall(r"#neatHack", posts, re.I))
    add("PASS" if n >= 3 else "WARN", "public #neatHack posts logged", f"{n} mention(s) in evidence/posts.md")
    vids = list((ROOT / "evidence" / "demo").glob("*.mp4")) if (ROOT / "evidence" / "demo").exists() else []
    if vids:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(vids[0])],
            capture_output=True, text=True,
        ).stdout.strip()  # fmt: skip
        try:
            dur = float(out)
            add("PASS" if dur <= 180 else "FAIL", "demo video <= 3:00", f"{dur:.0f}s")
        except ValueError:
            add("WARN", "demo video length", "could not read duration")
    else:
        add("WARN", "demo video", "none in evidence/demo/ yet")
    cfo = list((ROOT / "evidence" / "cfo").glob("*")) if (ROOT / "evidence" / "cfo").exists() else []
    add(
        "PASS" if any(p.suffix in (".md", ".json") for p in cfo) else "WARN",
        "cfo.ai plan evidence",
        f"{len(cfo)} file(s) in evidence/cfo/",
    )
    names = (
        {p.name for p in (ROOT / "evidence" / "traces").glob("*")} if (ROOT / "evidence" / "traces").exists() else set()
    )
    add("PASS" if names else "WARN", "exported traces", f"{len(names)} file(s)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    for fn in (check_commits, check_checkpoints, check_secrets, check_ledger, check_hardening, check_posts_video_cfo):
        try:
            fn()
        except Exception as e:
            add("FAIL", fn.__name__, f"{type(e).__name__}: {e}")
    width = max(len(n) for _, n, _ in results)
    for s, n, d in results:
        print(f"{s:4}  {n:{width}}  {d}")
    fails = sum(s == "FAIL" for s, *_ in results)
    warns = sum(s == "WARN" for s, *_ in results)
    print(f"\n{fails} FAIL, {warns} WARN, {sum(s == 'PASS' for s, *_ in results)} PASS")
    sys.exit(1 if fails or (a.strict and warns) else 0)


if __name__ == "__main__":
    main()
