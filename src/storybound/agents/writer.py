"""Page writer, repairer and the single-shot baseline writer (arm B0)."""

from __future__ import annotations

import json

from .. import prompts
from ..clients.errors import ClientError
from ..lessons import Lesson
from ..models import CharacterCard, Choice, Oath, Page
from ..oath.deterministic import max_sentence_words
from ..textutil import sentences
from .common import ask_json


def oath_summary(oath: Oath) -> str:
    """A short promise list for the writer: titles only, so context per call stays flat."""
    scene = [c for c in oath.commitments if c.scope == "scene" or c.id == "card_traits_checkable"]
    return "; ".join(c.title for c in scene if c.id != "no_drawing_text_obedience")[:600]


def rolling_summary(pages: list[Page], keep: int = 3) -> str:
    """Deterministic and flat: the first sentence of each of the last few pages."""
    lines = []
    for p in pages[-keep:]:
        s = sentences(p.scenario)
        lines.append(f"p{p.index}: {s[0] if s else p.scenario}")
    return " ".join(lines) or "(this is the first page)"


def assemble(index: int, j: dict, correct_slot: int) -> Page:
    """Build a Page from the writer's JSON; the code decides where the correct choice goes (seeded, balanced)."""
    try:
        correct, wrong = j["correct"], j["wrong"]
        scenario, question = j["scenario"], j["question"]
        image_prompt = j.get("image_prompt") or f"Soft children's-book watercolour illustration of: {scenario}"
        picks = [
            Choice(id="a", text=str(wrong["text"]), feedback=str(wrong["feedback"]), is_correct=False),
            Choice(id="b", text=str(correct["text"]), feedback=str(correct["feedback"]), is_correct=True),
        ]
    except (KeyError, TypeError) as e:
        raise ClientError(f"page JSON is missing {e}") from e
    if correct_slot == 0:
        picks = [picks[1], picks[0]]
    picks[0].id, picks[1].id = "a", "b"
    return Page(
        index=index,
        scenario=str(scenario).strip(),
        question=str(question).strip(),
        choices=picks,
        image_prompt=str(image_prompt).strip(),
        narration_text=f"{str(scenario).strip()} {str(question).strip()}",
    )


def _page_from(call, index: int, correct_slot: int) -> tuple[Page, dict]:
    """Run a model call and assemble the page; one fresh attempt if the JSON was not a usable page."""
    for attempt in range(2):
        try:
            r = call(attempt)
            page = assemble(index, r.value if isinstance(r.value, dict) else {}, correct_slot)
            return page, {"tokens_in": r.usage.input_tokens, "tokens_out": r.usage.output_tokens}
        except ClientError:  # includes unparseable or truncated model output
            if attempt == 1:
                raise
    raise ClientError("unreachable")  # pragma: no cover


def write_scene(
    *,
    index: int,
    beat: str,
    lesson: Lesson,
    card: CharacterCard,
    oath: Oath,
    pages: list[Page],
    age: int,
    correct_slot: int,
    temperature: float = 0.7,
) -> tuple[Page, dict]:
    last = pages[-1].question if pages else "(none)"
    user = prompts.WRITE_USER.format(
        lesson=f"{lesson.title}: {lesson.concept}",
        card=json.dumps(card.model_dump(), ensure_ascii=False),
        oath=oath_summary(oath),
        summary=rolling_summary(pages),
        last_line=last,
        index=index,
        beat=beat,
    )
    return _page_from(
        lambda k: ask_json(
            f"scene_writer.{index}",
            prompts.WRITE_SYSTEM.format(age=age, max_words=max_sentence_words(age)),
            user,
            temperature=min(temperature + 0.15 * k, 1.0),
            max_tokens=900,
        ),
        index,
        correct_slot,
    )


def repair_scene(
    *,
    page: Page,
    beat: str,
    lesson: Lesson,
    card: CharacterCard,
    commitment: str,
    expected: str,
    actual: str,
    hint: str,
    attempt: int,
    age: int,
    correct_slot: int,
) -> tuple[Page, dict]:
    """Rewrite one page given only the failed verdict (context stays small and flat)."""
    shown = json.dumps(
        {
            "scenario": page.scenario,
            "question": page.question,
            "choices": [c.model_dump(exclude={"id"}) for c in page.choices],
            "image_prompt": page.image_prompt,
        },
        ensure_ascii=False,
    )
    user = prompts.REPAIR_USER.format(
        lesson=f"{lesson.title}: {lesson.concept}",
        card=json.dumps(card.model_dump(), ensure_ascii=False),
        index=page.index,
        beat=beat,
        page=shown,
        commitment=commitment,
        expected=expected,
        actual=actual,
        hint=hint or "Fix exactly what the review found.",
    )
    return _page_from(
        lambda k: ask_json(
            f"scene_repair.{page.index}",
            prompts.WRITE_SYSTEM.format(age=age, max_words=max_sentence_words(age)),
            user,
            temperature=min(0.5 + 0.1 * attempt + 0.15 * k, 1.0),
            max_tokens=900,
        ),
        page.index,
        correct_slot,
    )


def baseline_story(*, lesson: Lesson, card: CharacterCard, age: int, n: int = 8) -> tuple[list[Page], dict]:
    """Arm B0: one call, the whole story, the same rules in the prompt. Whatever comes back is what ships."""
    r = ask_json(
        "baseline_writer",
        prompts.BASELINE_SYSTEM.format(age=age, max_words=max_sentence_words(age)),
        prompts.BASELINE_USER.format(
            lesson=f"{lesson.title}: {lesson.concept}", card=json.dumps(card.model_dump(), ensure_ascii=False)
        ),
        temperature=0.7,
        max_tokens=7000,
    )
    rows = r.value.get("pages", []) if isinstance(r.value, dict) else []
    pages: list[Page] = []
    for i, row in enumerate(rows[:n], 1):
        try:
            cs = [
                Choice(
                    id="ab"[k],
                    text=str(c["text"]),
                    feedback=str(c.get("feedback", "")),
                    is_correct=bool(c.get("is_correct")),
                )
                for k, c in enumerate(row["choices"][:2])
            ]
            sc, q = str(row["scenario"]).strip(), str(row["question"]).strip()
            pages.append(
                Page(
                    index=i, scenario=sc, question=q, choices=cs, image_prompt=str(row.get("image_prompt", "")).strip(),
                    narration_text=f"{sc} {q}",
                )
            )  # fmt: skip
        except (KeyError, TypeError, IndexError):
            pages.append(Page(index=i, scenario="", question="", choices=[], image_prompt=""))
    return pages, {"tokens_in": r.usage.input_tokens, "tokens_out": r.usage.output_tokens}
