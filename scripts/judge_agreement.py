"""Do judges from other model families agree with the K2 judge? A use of the hackathon gateway credits that adds evidence.

  python scripts/judge_agreement.py --source evidence/runs/<run>.json --bias evidence/runs/<judge-bias run>.json [--models claude-haiku,claude-sonnet-4.6,claude-opus-4.6]

Takes the same pages as scripts/judge_bias.py (clean, swapped answer, scary passage), sends the same promises and text to each gateway model
as the judge, and compares every promise verdict with K2's verdict from the bias run (`base`) and with the ground truth by construction
(a clean page should pass; the swapped page should be caught by correct_choice_teaches_lesson; the scary page by story_safe_text).
Not a human label: these are model-to-model numbers, and the note says so.
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
sys.path.insert(0, str(ROOT / "scripts"))

from storybound import ledger, tracing  # noqa: E402

tracing.init()

from eval_judge import mutate  # noqa: E402
from judge_bias import capture  # noqa: E402

from storybound.config import get_settings  # noqa: E402
from storybound.models import CharacterCard, Page  # noqa: E402
from storybound.oath.judge import judge_batch  # noqa: E402

TARGET = {"swap": "correct_choice_teaches_lesson", "scary": "story_safe_text"}
BAD = {"violation", "critical"}


def verdicts_with(model: str, items, text, ctx) -> dict[str, str]:
    return {cid: o.status for cid, o in judge_batch(items, text, ctx).items()}  # the judge model is set by main(), once per model


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--bias", required=True)
    ap.add_argument("--models", default="claude-haiku,claude-sonnet-4.6,claude-opus-4.6")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--name", default="judge-agreement")
    a = ap.parse_args()
    evs = json.loads(Path(a.source).read_text(encoding="utf-8"))["events"]
    card = CharacterCard(**next(e["data"]["card"] for e in evs if e["type"] == "character.ready"))
    pages = [Page(**e["data"]["page"]) for e in evs if e["type"] == "scene.accepted"]
    lesson_id = next(e["data"]["lesson_id"] for e in evs if e["type"] == "run.started")
    k2_rows = json.loads(Path(a.bias).read_text(encoding="utf-8"))["rows"]  # same order as jobs: for each page, clean / swap / scary
    kinds = ["clean", "swap", "scary"]
    jobs = [(p if k == "clean" else mutate(p, k, card.name), k) for p in pages for k in kinds]
    cells: list[dict] = []
    saved = get_settings().models.judge
    for model in a.models.split(","):
        get_settings().models.judge = model  # the judge client reads this per call: set once per model, restored after the loop
        with cf.ThreadPoolExecutor(max_workers=a.workers) as pool:
            futs = []
            for (page, kind), row in zip(jobs, k2_rows, strict=True):
                items, text, ctx = capture(page, card, lesson_id)
                futs.append((kind, row, items, pool.submit(contextvars.copy_context().run, verdicts_with, model, items, text, ctx)))
            for kind, row, items, f in futs:
                got = f.result()
                for c in items:
                    cells.append({"model": model, "kind": kind, "promise": c.id, "model_status": got.get(c.id), "k2_status": row["base"].get(c.id)})
    get_settings().models.judge = saved
    out_models = {}
    for model in a.models.split(","):
        # a verification_error is not a pass: errors are left out of both sides of every ratio (and counted separately below)
        cs = [c for c in cells if c["model"] == model and c["model_status"] not in (None, "verification_error") and c["k2_status"] not in (None, "verification_error")]
        agree = sum(1 for c in cs if (c["model_status"] in BAD) == (c["k2_status"] in BAD))
        truth = [c for c in cs if (c["kind"] == "clean") or c["promise"] == TARGET.get(c["kind"])]
        right = sum(1 for c in truth if (c["model_status"] in BAD) == (c["kind"] != "clean"))
        k2_right = sum(1 for c in truth if (c["k2_status"] in BAD) == (c["kind"] != "clean"))
        out_models[model] = {
            "cells": len(cs), "agree_with_k2": f"{agree}/{len(cs)}", "ground_truth_cells": len(truth),
            "model_matches_ground_truth": f"{right}/{len(truth)}", "k2_matches_ground_truth": f"{k2_right}/{len(truth)}",
            "disagreements": sorted({c["promise"] for c in cs if (c["model_status"] in BAD) != (c["k2_status"] in BAD)}),
            "errors": sum(1 for c in cells if c["model"] == model and c["model_status"] == "verification_error"),
        }  # fmt: skip
    summary = {"source": Path(a.source).name, "pages": len(pages), "variants": kinds, "models": out_models}
    print(json.dumps(summary, indent=2))
    out = ROOT / "evidence" / "runs" / f"{ledger.stamp(a.name)}.json"
    out.write_text(json.dumps({"summary": summary, "cells": cells}, indent=1), encoding="utf-8")
    ledger.append({"name": a.name, "kind": "judge-agreement", "summary": summary, "file": out.name})
    tracing.flush()


if __name__ == "__main__":
    main()
