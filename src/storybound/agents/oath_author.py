"""Oath author: the fixed core plus lesson-specific promises, written and hashed before any story text exists."""

from __future__ import annotations

import json

from .. import prompts
from ..clients.errors import ClientError
from ..lessons import Lesson
from ..models import CharacterCard, Oath
from ..oath import catalog
from .common import ask_json


def author(lesson: Lesson, card: CharacterCard) -> tuple[Oath, dict]:
    base = catalog.core_oath()
    info: dict = {"rejected": [], "added": [], "tokens_in": 0, "tokens_out": 0, "author_failed": False}
    try:
        r = ask_json(
            "oath_author",
            prompts.OATH_SYSTEM,
            prompts.OATH_USER.format(
                lesson=f"{lesson.title}: {lesson.concept}", card=json.dumps(card.model_dump(), ensure_ascii=False)
            ),
            temperature=0.3,
            max_tokens=900,
        )
        adds = r.value.get("additions", []) if isinstance(r.value, dict) else []
        oath, rejected = catalog.merge_additions(base, [a for a in adds if isinstance(a, dict)])
        info.update(
            rejected=rejected,
            added=[c.id for c in oath.commitments if not c.core],
            tokens_in=r.usage.input_tokens,
            tokens_out=r.usage.output_tokens,
        )
        return oath, info
    except ClientError:
        info["author_failed"] = True  # the core oath alone is still a complete oath
        return base, info
