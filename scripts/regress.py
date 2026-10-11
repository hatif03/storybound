"""A frozen set of past failures, re-run on the current code (the idea from SWE-bench: every case is one record with its input and its pass condition).

  python scripts/regress.py --build                       # freeze cases from evidence/ledger.jsonl into evidence/regression/cases.jsonl
  python scripts/regress.py --run [--name regress-1] [--only age_reading_level,story_safe_text] [--limit 6] [--workers 3]

A case is a story job (drawing, lesson, seed, age) whose FIRST PASS broke a promise at some point in the project, with the promise that broke
(`must_flip`), the prompt version it broke on, and the trace that shows it. Re-running it on today's code gives three outcomes, kept apart:
  resolved      the story shipped with every promise kept (`shipped_violations == 0`)
  unresolved    the story shipped with a break on the receipt (a regression)
  error         no result (a provider error, for example): never counted as resolved or as a failure
and one more fact per case: whether the same promise broke again on the first pass (`first_pass_again`), which tells you the weakness is still
there and the gate is what catches it. Pictures and narration are off. One ledger row per run.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import contextvars
import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from storybound import ledger, media, tracing  # noqa: E402

tracing.init()

from storybound.events import EventLog  # noqa: E402
from storybound.pipeline import Run, RunConfig, execute, ledger_row  # noqa: E402

FIX = ROOT / "assets" / "test-drawings"
CASES = ROOT / "evidence" / "regression" / "cases.jsonl"
SWEEPS = ("sweep-1-p1", "sweep-2-p2", "sweep-4-p3", "sweep-5-hr45", "sweep-6-t90", "sweep-7-quiz")


def family(promise: str) -> str:
    return "lesson_specific" if promise.startswith("lesson_specific_") else promise


def build(per_family: int = 2) -> None:
    rows = [r for r in ledger.read() if r.get("arm") == "B1" and r.get("name") in SWEEPS and r.get("first_pass_failed") and not r.get("error")]
    seen: dict[str, int] = {}
    cases = []
    for r in rows:  # earliest first: the failure as it first appeared
        for promise in r["first_pass_failed"]:
            fam = family(promise)
            if seen.get(fam, 0) >= per_family or any(c["fixture"] == r["fixture"] and c["lesson"] == r["lesson"] and c["must_flip"] == promise for c in cases):
                continue
            seen[fam] = seen.get(fam, 0) + 1
            cases.append({
                "case_id": f"rc-{len(cases) + 1:02d}", "must_flip": promise, "family": fam, "fixture": r["fixture"], "lesson": r["lesson"],
                "seed": str(r["seed"]), "age": int(r.get("age") or 6), "arm": "B1", "failed_on_prompt": r.get("prompt_version"),
                "found_in": r["name"], "trace_id": r.get("trace_id"), "split": ledger.split_of(r["fixture"]),
                "must_stay_green": "every other promise of the oath, and shipped_violations == 0",
            })  # fmt: skip
    CASES.parent.mkdir(parents=True, exist_ok=True)
    CASES.write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in cases), encoding="utf-8")
    print(f"froze {len(cases)} cases from {len(rows)} ledger rows into {CASES.relative_to(ROOT)}")


def fixture_path(fid: str) -> Path:
    for ext in ("", ".png", ".jpg"):
        if (FIX / (fid + ext)).is_file():
            return FIX / (fid + ext)
    sys.exit(f"unknown fixture {fid}")


def run_case(name: str, c: dict) -> dict:
    d = media.prepare(fixture_path(c["fixture"]).read_bytes())
    cfg = RunConfig(lesson_id=c["lesson"], age=c["age"], arm="B1", seed=c["seed"], media=False, fixture=c["fixture"], ledger_name=name)
    run = Run(cfg=cfg, drawing=d, bus=EventLog(), story_id=uuid.uuid4().hex[:12])
    execute(run)
    row = ledger_row(run)
    if run.error or run.outcome not in ("shipped", "shipped_with_notes"):
        status = "error" if run.error or run.outcome in ("error", "") else "refused"
    else:
        status = "resolved" if not run.shipped else "unresolved"
    res = {
        "case_id": c["case_id"], "must_flip": c["must_flip"], "status": status, "first_pass_again": c["must_flip"] in (row.get("first_pass_failed") or []),
        "first_pass_failed": row.get("first_pass_failed"), "shipped": [s.get("commitment") for s in run.shipped], "outcome": run.outcome,
        "repairs": (row.get("counts") or {}).get("repairs"), "trace_id": run.trace_id, "prompt_version": row.get("prompt_version"), "error": run.error or None,
    }  # fmt: skip
    print(f"{c['case_id']} {c['must_flip'][:38]:38} {status:10} first-pass-again={res['first_pass_again']} repairs={res['repairs']}", flush=True)
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--name", default="regress-1")
    ap.add_argument("--only", default="", help="comma list of promise ids or families")
    ap.add_argument("--ids", default="", help="comma list of case ids, e.g. rc-03,rc-05")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    if a.build:
        build()
    if not a.run:
        return
    cases = [json.loads(x) for x in CASES.read_text(encoding="utf-8").splitlines() if x.strip()]
    if a.only:
        want = set(a.only.split(","))
        cases = [c for c in cases if c["must_flip"] in want or c["family"] in want]
    if a.ids:
        cases = [c for c in cases if c["case_id"] in set(a.ids.split(","))]
    if a.limit:
        cases = cases[: a.limit]
    with cf.ThreadPoolExecutor(max_workers=a.workers) as pool:
        futs = [pool.submit(contextvars.copy_context().run, run_case, a.name, c) for c in cases]
        results = []
        for f, c in zip(futs, cases, strict=True):
            try:
                results.append(f.result())
            except Exception as e:  # one broken job must not hide the others
                results.append({"case_id": c["case_id"], "must_flip": c["must_flip"], "status": "error", "error": f"{type(e).__name__}: {str(e)[:120]}"})
    n = len(results)
    by = {k: sum(1 for r in results if r["status"] == k) for k in ("resolved", "unresolved", "refused", "error")}
    summary = {"cases": n, **by, "first_pass_again": sum(1 for r in results if r.get("first_pass_again"))}
    print(json.dumps(summary))
    out = ROOT / "evidence" / "regression" / f"{ledger.stamp(a.name)}.json"
    out.write_text(json.dumps({"summary": summary, "results": results, "git_sha": ledger.git_sha()}, indent=1), encoding="utf-8")
    ledger.append({"name": a.name, "kind": "regression", "summary": summary, "file": out.name})
    tracing.flush()


if __name__ == "__main__":
    main()
