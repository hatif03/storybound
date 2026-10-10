"""The quiz maker: four questions about a finished story, each pointing at the line that answers it."""

from __future__ import annotations

from .. import prompts
from ..lessons import Lesson
from ..models import CharacterCard, Page, Quiz, QuizItem, QuizOption
from ..oath.deterministic import target_sentence_words
from .common import ask_json, rng

KINDS = ("recall", "order", "feeling", "lesson")


def _story_text(pages: list[Page]) -> str:
    return "\n".join(
        f"PAGE {p.index}: {p.scenario} Question: {p.question} " + " ".join(f"[{c.text}: {c.feedback}]" for c in p.choices) for p in pages
    )


def _item(raw: dict, index: int, seed: str) -> QuizItem:
    """Shuffle the answers with a seeded generator so the right one is not always first."""
    texts = [(str(raw["correct"]).strip(), True), *[(str(w).strip(), False) for w in list(raw["wrong"])[:2]]]
    rng(seed, "quiz", index).shuffle(texts)
    return QuizItem(
        index=index, kind=raw.get("kind", KINDS[(index - 1) % 4]), question=str(raw["question"]).strip(),
        options=[QuizOption(id="abc"[i], text=t, is_correct=ok) for i, (t, ok) in enumerate(texts)],
        evidence_page=int(raw["evidence_page"]), evidence_quote=str(raw["evidence_quote"]).strip(),
        explain=str(raw.get("explain", "")).strip(),
    )  # fmt: skip


def make_quiz(pages: list[Page], card: CharacterCard, lesson: Lesson, age: int, seed: str) -> Quiz:
    system = prompts.QUIZ_SYSTEM.format(age=age, lesson=lesson.title.lower(), max_words=target_sentence_words(age))
    user = f"Hero: {card.name} the {card.species}.\n\nSTORY\n{_story_text(pages)}"
    r = ask_json("quiz_maker", system, user, temperature=0.4, max_tokens=2500)
    items = []
    for i, raw in enumerate(r.value.get("items", [])[:4], 1):
        try:
            items.append(_item(raw, i, seed))
        except Exception:  # a malformed item is dropped, never fatal
            continue
    return Quiz(items=items, talk_about=str(r.value.get("talk_about", "")).strip()[:200])


def repair_item(q: QuizItem, failures: str, pages: list[Page], age: int, seed: str) -> QuizItem:
    system = prompts.QUIZ_REPAIR_SYSTEM.format(age=age, max_words=target_sentence_words(age))
    user = (f"Quiz item (kind {q.kind}):\n{q.model_dump_json()}\n\nFailure: {failures}\n\nSTORY\n{_story_text(pages)}\n\n"
            f"Use evidence_page {q.evidence_page} or a better page. Keep kind '{q.kind}'.")  # fmt: skip
    r = ask_json(f"quiz_repair.{q.index}", system, user, temperature=0.3, max_tokens=900)
    raw = r.value if isinstance(r.value, dict) else {}
    raw = raw.get("items", [raw])[0] if isinstance(raw.get("items"), list) and raw["items"] else raw
    raw.setdefault("kind", q.kind)
    return _item(raw, q.index, seed + "r")
