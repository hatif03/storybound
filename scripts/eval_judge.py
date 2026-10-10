"""Judge check with ground truth by construction: clean pages versus pages with one injected fault.

  python scripts/eval_judge.py --source evidence/runs/<run>.json [--name judge-eval]

Takes the accepted pages of a real run (all passed the oath), then makes copies with one known fault each:
  swap       the correct and wrong choice flags are swapped (the right answer no longer teaches the lesson)
  off-topic  the page is rewritten to be about something unrelated to the lesson
  scary      a deterministic-clean but frightening passage is added (no blocked words)
Clean pages must pass; faulted pages must be caught by the matching promise. Reports recall (faults caught) and the
false-alarm rate (clean pages flagged), with the quote check on every judged verdict. Sampling is forced to 1.0 here.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import contextvars
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from storybound import ledger, lessons, tracing  # noqa: E402

tracing.init()

import neatlogs  # noqa: E402

from storybound.models import CharacterCard, Page  # noqa: E402
from storybound.oath import catalog  # noqa: E402
from storybound.oath import deterministic as d  # noqa: E402
from storybound.oath.engine import Engine  # noqa: E402

FAULTS = {
    "swap": "correct_choice_teaches_lesson",
    "off-topic": "lesson_concept_in_scene",
    "scary": "story_safe_text",
}


def mutate(p: Page, kind: str, name: str) -> Page:
    q = p.model_copy(deep=True)
    if kind == "swap":
        for c in q.choices:
            c.is_correct = not c.is_correct
    elif kind == "off-topic":
        q.scenario = f"{name} counts the clouds and thinks about how many stars there are in the sky tonight."
        q.question = f"How many clouds can {name} count?"
        q.choices[0].text, q.choices[0].feedback = "Count to ten slowly.", "Ten is a nice round number."
        q.choices[1].text, q.choices[1].feedback = "Count to twenty.", "Twenty is even bigger."
    elif kind == "scary":
        q.scenario = (
            f"{name} walks alone into the dark, silent forest where something huge growls in the shadows. "
            f"{name} shakes with fear and cannot find the way home."
        )
    return q


@neatlogs.span(kind="WORKFLOW", name="judge-eval-one")
def one(page: Page, kind: str, card: CharacterCard, lesson_id: str) -> dict:
    ctx = d.Ctx(card=card, lesson=lessons.get(lesson_id), age=6, seed="judge-eval")
    eng = Engine(oath=catalog.core_oath(), ctx=ctx, rates={"quality": 1.0, "image": 1.0})
    vs = {v.commitment: v for v in eng.verify_scene(page, 0)}
    target = FAULTS.get(kind)
    flagged = {c for c, v in vs.items() if v.status in ("violation", "critical")}
    judged = [v for v in vs.values() if v.verdict_by in ("judge", "both")]
    return {
        "page": page.index, "kind": kind, "target": target,
        "caught": (target in flagged) if target else None,
        "flagged": sorted(flagged),
        "judge_errors": sum(1 for v in judged if v.judge_status == "verification_error"),
        "judged": len(judged),
        "by": {c: v.verdict_by for c, v in vs.items() if c in FAULTS.values()},
    }  # fmt: skip


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--name", default="judge-eval")
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    data = json.loads(Path(a.source).read_text(encoding="utf-8"))
    evs = data["events"]
    card = CharacterCard(**next(e["data"]["card"] for e in evs if e["type"] == "character.ready"))
    pages = [Page(**e["data"]["page"]) for e in evs if e["type"] == "scene.accepted"]
    lesson_id = next(e["data"]["lesson_id"] for e in evs if e["type"] == "run.started")
    jobs = [(p, "clean") for p in pages] + [(mutate(p, k, card.name), k) for p in pages for k in FAULTS]
    with cf.ThreadPoolExecutor(max_workers=a.workers) as pool:
        futs = [pool.submit(contextvars.copy_context().run, one, p, k, card, lesson_id) for p, k in jobs]
        rows = [f.result() for f in futs]
    clean = [r for r in rows if r["kind"] == "clean"]
    summary = {"pages": len(pages), "lesson": lesson_id}
    summary["false_alarms"] = f"{sum(1 for r in clean if r['flagged'])}/{len(clean)}"
    for k, target in FAULTS.items():
        rs = [r for r in rows if r["kind"] == k]
        summary[f"{k} caught by {target}"] = f"{sum(1 for r in rs if r['caught'])}/{len(rs)}"
    summary["judge_errors"] = f"{sum(r['judge_errors'] for r in rows)}/{sum(r['judged'] for r in rows)}"
    print(json.dumps(summary, indent=2))
    out = ROOT / "evidence" / "runs" / f"{ledger.stamp(a.name)}.json"
    out.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2), encoding="utf-8")
    ledger.append({"name": a.name, "kind": "judge-eval", "summary": summary, "file": out.name})
    tracing.flush()


if __name__ == "__main__":
    main()
