"""Generate EVIDENCE.md from the ledger and the evidence folders. Nothing here is typed by hand: re-run after every change.

python scripts/build_evidence.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from storybound import ledger  # noqa: E402

EV = ROOT / "evidence"


def rel(p: Path) -> str:
    return str(p.relative_to(ROOT)).replace("\\", "/")


def latest(pattern: str, folder: Path = EV / "runs") -> Path | None:
    files = sorted(folder.glob(pattern))
    return files[-1] if files else None


def git(*a: str) -> str:
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, encoding="utf-8").stdout


def section_agent() -> list[str]:
    L = ["## 1. The agent improved: before and after, with numbers", ""]
    recs = sorted((EV / "hardening").glob("HR-*.md"))
    if not recs:
        L.append("No hardening record yet.")
    for r in recs:
        text = r.read_text(encoding="utf-8")
        title = text.splitlines()[0].lstrip("# ").strip()
        L.append(f"- [{title}]({rel(r)})")
    L.append("")
    reports = sorted((EV / "reports").glob("*.md"))
    for r in reports:
        L.append(f"- Sweep report: [{r.stem}]({rel(r)})")
    for r in (r for r in reports if "sweep" in r.name):
        L += ["", f"### {r.stem}", ""] + r.read_text(encoding="utf-8").splitlines()[2:30]
    return L + [""]


def section_traces() -> list[str]:
    L = ["## 2. neatlogs traces", ""]
    rows = [r for r in ledger.read() if r.get("trace_id")]
    L.append(
        f"{len(rows)} ledger rows carry a neatlogs trace id. Exported readbacks are in `evidence/traces/` (read through the neatlogs MCP server)."
    )
    L += ["", "| What | Trace id | File |", "| --- | --- | --- |"]
    for p in sorted((EV / "traces").glob("*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            text = d["result"]["content"][0]["text"]
            tid = json.loads(text).get("trace_id") or ""
        except Exception:
            tid = ""
        L.append(f"| {p.stem[18:]} | `{tid}` | [{p.name}]({rel(p)}) |")
    return L + [""]


def section_recovery() -> list[str]:
    L = ["## 3. A recovery run: an action failed, what the agent did next", ""]
    f = latest("*image-429-recovery.json")
    if f:
        d = json.loads(f.read_text(encoding="utf-8"))
        deg = d["receipt"]["degradations"]
        L += [
            d["note"],
            "",
            f"- File: [{f.name}]({rel(f)}); neatlogs trace `{d['receipt']['trace_id']}`",
            f"- Degradations on the receipt: {len(deg)} (`{deg[0]['what']}`: {deg[0]['why'][:60]}...) -> `{deg[0]['fallback']}`",
            f'- Receipt line: "{d["receipt"]["plain"]}"',
        ]
    rows = [r for r in ledger.read() if r.get("arm") == "B1" and (r.get("counts") or {}).get("repairs", 0) > 0]
    L += [
        "",
        f"Repair recoveries inside the story loop: {len(rows)} gated runs repaired at least one page (see the sweep report).",
    ]
    return L + [""]


def section_safety_judge() -> list[str]:
    L = ["## 4. Safety screen and judge checks", ""]
    for label, pat in (
        ("Safety screen over the 26 fixture drawings", "*safety-eval*.json"),
        ("Judge with injected faults", "*judge-eval*.json"),
    ):
        fs = sorted((EV / "runs").glob(pat))
        for f in fs:
            d = json.loads(f.read_text(encoding="utf-8"))
            L.append(f"- {label}, `{f.name}`: {json.dumps(d['summary'], ensure_ascii=False)}")
    return L + [""]


def section_detections() -> list[str]:
    L = ["## 5. neatlogs detections", ""]
    f = latest("*detections*.json", EV / "traces")
    if f:
        d = json.loads(json.loads(f.read_text(encoding="utf-8"))["result"]["content"][0]["text"])
        for x in d["detections"]:
            L.append(f"- **{x['display_name']}** ({x['type']}): {x['description']}")
    return L + [""]


def section_entire() -> list[str]:
    L = ["## 6. Entire", ""]
    log = git("log", "--format=%h|%(trailers:key=Entire-Checkpoint,valueonly)|%s")
    rows = [line.split("|", 2) for line in log.splitlines() if line.count("|") >= 2]
    linked = [r for r in rows if r[1].strip()]
    L.append(f"- Commits: {len(rows)}; with an `Entire-Checkpoint` trailer: {len(linked)}.")
    for r in linked[:20]:
        L.append(f"  - `{r[0]}` checkpoint `{r[1].strip()}`: {r[2][:70]}")
    for p in sorted((EV / "entire").glob("*")):
        if p.name != ".gitkeep":
            L.append(f"- Graph output: [{p.name}]({rel(p)})")
    return L + [""]


def section_business() -> list[str]:
    L = ["## 7. cfo.ai business plan", ""]
    files = [p for p in (EV / "cfo").glob("*") if p.name != ".gitkeep"] if (EV / "cfo").exists() else []
    if files:
        L += [f"- [{p.name}]({rel(p)})" for p in files]
    else:
        L.append("Not yet linked.")
    bi = ROOT / "docs" / "BUSINESS_INPUTS.md"
    if bi.exists():
        L.append(f"- Measured inputs for the model: [{bi.name}](docs/BUSINESS_INPUTS.md)")
    return L + [""]


def section_public() -> list[str]:
    L = ["## 8. Public posts and repository", ""]
    posts = EV / "posts.md"
    n = len(re.findall(r"#neatHack", posts.read_text(encoding="utf-8"), re.I)) if posts.exists() else 0
    L.append(f"- Posts logged with #neatHack: {n} ([evidence/posts.md](evidence/posts.md)).")
    first = git("log", "--reverse", "--format=%aI", "-1").strip()
    last = git("log", "--format=%aI", "-1").strip()
    L.append(f"- First commit {first}; latest {last}. Window check: `python scripts/lint_evidence.py`.")
    return L + [""]


def main() -> None:
    rows = ledger.read()
    runs = [r for r in rows if r.get("arm")]
    head = [
        "# EVIDENCE",
        "",
        f"Generated {ledger.now_ist():%Y-%m-%d %H:%M} IST by `scripts/build_evidence.py` from `evidence/ledger.jsonl` ({len(rows)} rows, {len(runs)} story runs) and the folders under `evidence/`. Do not edit by hand.",
        "",
        "Each result is a triple: the commit that produced it, the Entire checkpoint of the session (when the session was recorded), and the neatlogs trace.",
        "",
    ]
    out = head
    for fn in (
        section_agent,
        section_traces,
        section_recovery,
        section_safety_judge,
        section_detections,
        section_entire,
        section_business,
        section_public,
    ):
        out += fn()
    (ROOT / "EVIDENCE.md").write_text("\n".join(out), encoding="utf-8")
    print("wrote EVIDENCE.md", len(out), "lines")


if __name__ == "__main__":
    main()
