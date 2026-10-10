"""Story planner: eight beats, each with a setting, an event, a temptation and the right choice."""

from __future__ import annotations

import json

from .. import prompts
from ..clients.errors import ClientError
from ..lessons import Lesson
from ..models import CharacterCard
from .common import ask_json


def plan(lesson: Lesson, card: CharacterCard, age: int, n: int = 8) -> tuple[list[dict], dict]:
    for attempt in range(2):
        r = ask_json(
            "story_planner",
            prompts.PLAN_SYSTEM.format(age=age),
            prompts.PLAN_USER.format(
                lesson=f"{lesson.title}: {lesson.concept}", card=json.dumps(card.model_dump(), ensure_ascii=False)
            ),
            temperature=0.6 + 0.1 * attempt,
            max_tokens=1800,
        )
        beats = r.value.get("beats", []) if isinstance(r.value, dict) else r.value if isinstance(r.value, list) else []
        beats = [b for b in beats if isinstance(b, dict)]
        if len(beats) >= n:
            beats = beats[:n]
            for i, b in enumerate(beats, 1):
                b["index"] = i
            return beats, {"tokens_in": r.usage.input_tokens, "tokens_out": r.usage.output_tokens}
    raise ClientError("planner did not return eight beats")


def beat_text(b: dict) -> str:
    return (
        f"setting: {b.get('setting', '')}; event: {b.get('event', '')}; temptation: {b.get('temptation', '')}; "
        f"the right choice: {b.get('right_choice', '')}"
    )
