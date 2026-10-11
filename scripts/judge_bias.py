"""Does the judge change its mind for reasons that are not about the page? Two biases from OpenAI's evaluation guide, tested on our judge.

  python scripts/judge_bias.py --source evidence/runs/<run>.json [--name judge-bias]

Position bias: the same page and the same promises, sent in three different orders (as written, reversed, shuffled). A promise whose
verdict flips with the order is order-dependent.
Length bias: the same page with two harmless sentences added (about twice the words). A clean page must stay clean; a page with an injected
fault (swap, scary) must stay caught. A verdict that flips with padding is length-dependent.
Every verdict is the judge's own (sampling forced to 1.0). Pages come from a real run that already passed the oath; faults are the ones in
scripts/eval_judge.py.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import contextvars
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from storybound import ledger, lessons, tracing  # noqa: E402

tracing.init()

import neatlogs  # noqa: E402
from eval_judge import mutate  # noqa: E402

from storybound.models import CharacterCard, Page  # noqa: E402
from storybound.oath import catalog  # noqa: E402
from storybound.oath import deterministic as d  # noqa: E402
from storybound.oath.engine import Engine  # noqa: E402
from storybound.oath.judge import judge_batch  # noqa: E402

PAD = " The morning was warm and bright. A soft breeze moved the tall green grass."


def pad(p: Page) -> Page:
    q = p.model_copy(deep=True)
    q.scenario = q.scenario.rstrip() + PAD
    return q


def capture(page: Page, card: CharacterCard, lesson_id: str):
    """What the engine would send to the judge for this page: (promises, text, context)."""
    got: dict = {}

    def recorder(items, text, ctx):
        got.update(items=items, text=text, ctx=ctx)
        return {}

    ctx = d.Ctx(card=card, lesson=lessons.get(lesson_id), age=6, seed="judge-bias")
    eng = Engine(oath=catalog.core_oath(), ctx=ctx, rates={"quality": 1.0, "image": 1.0}, judge=recorder)
    eng.verify_scene(page, 0)
    return got.get("items", []), got.get("text", ""), got.get("ctx", {})


def verdicts(items, text, ctx) -> dict[str, str]:
    out = judge_batch(items, text, ctx)
    return {cid: o.status for cid, o in out.items()}


@neatlogs.span(kind="WORKFLOW", name="judge-bias-one")
def one(page: Page, kind: str, card: CharacterCard, lesson_id: str, seed: int) -> dict:
    items, text, ctx = capture(page, card, lesson_id)
    shuffled = items[:]
    random.Random(seed).shuffle(shuffled)
    base = verdicts(items, text, ctx)
    rev = verdicts(items[::-1], text, ctx)
    shuf = verdicts(shuffled, text, ctx)
    p_items, p_text, p_ctx = capture(pad(page), card, lesson_id)
    padded = verdicts(p_items, p_text, p_ctx)
    order_flips = sorted({c for c in base if rev.get(c) != base[c] or shuf.get(c) != base[c]})
    pad_flips = sorted({c for c in base if padded.get(c) != base[c]})
    return {
        "page": page.index, "kind": kind, "promises": len(items), "words": len(text.split()), "padded_words": len(p_text.split()),
        "base": base, "order_flips": order_flips, "pad_flips": pad_flips,
        "errors": sum(1 for v in [*base.values(), *rev.values(), *shuf.values(), *padded.values()] if v == "verification_error"),
    }  # fmt: skip


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--name", default="judge-bias")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--faults", default="swap,scary")
    a = ap.parse_args()
    evs = json.loads(Path(a.source).read_text(encoding="utf-8"))["events"]
    card = CharacterCard(**next(e["data"]["card"] for e in evs if e["type"] == "character.ready"))
    pages = [Page(**e["data"]["page"]) for e in evs if e["type"] == "scene.accepted"]
    lesson_id = next(e["data"]["lesson_id"] for e in evs if e["type"] == "run.started")
    kinds = ["clean", *[k for k in a.faults.split(",") if k]]
    jobs = [(p if k == "clean" else mutate(p, k, card.name), k) for p in pages for k in kinds]
    with cf.ThreadPoolExecutor(max_workers=a.workers) as pool:
        futs = [pool.submit(contextvars.copy_context().run, one, p, k, card, lesson_id, i) for i, (p, k) in enumerate(jobs)]
        rows = [f.result() for f in futs]
    n_cells = sum(r["promises"] for r in rows)
    summary = {
        "lesson": lesson_id, "pages": len(pages), "variants": kinds, "page_runs": len(rows), "verdict_cells": n_cells,
        "judge_errors": sum(r["errors"] for r in rows),
        "order_flips": f"{sum(len(r['order_flips']) for r in rows)}/{n_cells} promise verdicts changed with the order",
        "pad_flips": f"{sum(len(r['pad_flips']) for r in rows)}/{n_cells} promise verdicts changed with two added sentences",
        "pages_with_an_order_flip": f"{sum(1 for r in rows if r['order_flips'])}/{len(rows)}",
        "pages_with_a_padding_flip": f"{sum(1 for r in rows if r['pad_flips'])}/{len(rows)}",
        "flipped_promises": sorted({c for r in rows for c in (*r["order_flips"], *r["pad_flips"])}),
        "mean_words_added": round(sum(r["padded_words"] - r["words"] for r in rows) / max(1, len(rows)), 1),
    }  # fmt: skip
    print(json.dumps(summary, indent=2))
    out = ROOT / "evidence" / "runs" / f"{ledger.stamp(a.name)}.json"
    out.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2), encoding="utf-8")
    ledger.append({"name": a.name, "kind": "judge-bias", "summary": summary, "file": out.name})
    tracing.flush()


if __name__ == "__main__":
    main()
