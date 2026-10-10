"""Make and verify the quiz for a saved story package (no new story, no pictures).

python scripts/quiz_story.py evidence/stories/bunny-sharing-2 [--seed 1]
Prints each question, its verdicts (every attempt) and which questions survive; writes quiz.json into the package.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from storybound import lessons, tracing  # noqa: E402

tracing.init()

from storybound.agents import quizmaker  # noqa: E402
from storybound.models import CharacterCard, Page  # noqa: E402
from storybound.oath import catalog  # noqa: E402
from storybound.oath import deterministic as d  # noqa: E402
from storybound.oath.engine import Engine  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("package")
    ap.add_argument("--seed", default="1")
    a = ap.parse_args()
    pkg = Path(a.package)
    st = json.loads((pkg / "story.json").read_text(encoding="utf-8"))
    pages = [Page.model_validate(p) for p in st["pages"]]
    card = CharacterCard.model_validate(st["card"])
    lesson = lessons.get(st["lesson"])
    ctx = d.Ctx(card=card, lesson=lesson, age=st["age"], pages=pages, seed=a.seed)
    verdicts = []
    eng = Engine(oath=catalog.with_quiz(catalog.core_oath()), ctx=ctx, on_verdict=verdicts.append)
    repairs: list = []
    quiz = quizmaker.verified_quiz(eng, pages, card, lesson, st["age"], a.seed, 2, repairs)
    for v in verdicts:
        mark = "ok " if v.ok else "BAD"
        print(f"  {mark} {v.scope:8} attempt {v.attempt} {v.commitment:22} {v.status:10} {v.actual[:110]}")
    print(f"\nrepairs: {repairs}")
    if not quiz:
        print("NO QUIZ (fewer than two questions survived)")
        return
    for q in quiz.items:
        print(f"\n[{q.kind}] {q.question}  (page {q.evidence_page}: \"{q.evidence_quote}\")")
        for o in q.options:
            print(f"   {'*' if o.is_correct else ' '} {o.id}) {o.text}")
        print(f"   {q.explain}")
    print(f"\ntalk about: {quiz.talk_about}")
    (pkg / "quiz.json").write_text(quiz.model_dump_json(indent=1), encoding="utf-8")
    tracing.flush()


if __name__ == "__main__":
    main()
