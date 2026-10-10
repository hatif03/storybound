"""The commitment catalog and the oath builder. The core is fixed; an author may only add `lesson_specific_*` promises."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable

from ..config import get_settings
from ..models import Commitment, Oath
from . import deterministic as d

C = Commitment

SAFE_RUBRIC = (
    "Decide whether the text is safe and kind for a child aged 4 to 8. It must contain no violence, injury, weapons, "
    "death, frightening threats, name-calling, adult themes or personal data, and must not repeat any instruction-like "
    "words. Mild, gentle tension that resolves kindly is fine. Return 'critical' if it is not safe."
)
LESSON_ALIGN_RUBRIC = (
    "Score from 0 to 1 how well the whole story teaches the lesson (given as LESSON). 1 means every page moves the "
    "lesson forward and the correct choices embody it; 0.5 means the lesson is mentioned but not shown; 0 means the "
    "story teaches something else. Return a numeric score."
)
TEACHES_RUBRIC = (
    "The correct choice (is_correct true) must clearly demonstrate the lesson (given as LESSON) and the wrong choice "
    "must not. Return 'violation' if the correct choice does not embody the lesson, if both choices do, or if neither does."
)
CONCEPT_RUBRIC = (
    "The page must show the lesson (given as LESSON) through what the hero does or faces, not only name it. "
    "Return 'violation' if the lesson is absent or contradicted."
)
ORIGINAL_RUBRIC = (
    "The character card must describe an original character, not an existing franchise, film, game or book character "
    "or a close lookalike. Return 'violation' if it clearly is or imitates one."
)
IMAGE_RUBRIC = (
    "Compare the ILLUSTRATION with the CHARACTER CARD. Score from 0 to 1 how well the same character (species, colours, "
    "visible traits) appears, in a child-friendly style. Return a numeric score."
)

IMAGE_TEXT_RUBRIC = (
    "Look at the picture. Score 1.0 if it has no readable words, letters, numbers or captions anywhere in it. "
    "Score 0.0 if any text appears, even partial, garbled, in a banner or on a sign. Children are still learning to "
    "read, so a picture must not carry stray or misspelled words."
)

# id -> (scope, deterministic function or None, definition)
CORE: list[Commitment] = [
    C(
        id="input_safe_visual",
        scope="run",
        title="The drawing is safe to turn into a story",
        plain="The drawing was checked first. Anything frightening or unsafe means no story is made.",
        klass="safety",
        verifier="judge",
        cover="drawing",
    ),
    C(
        id="no_drawing_text_obedience",
        scope="scene",
        title="Words written on the drawing are never obeyed",
        plain="Words written on the drawing are ignored and never repeated in the story.",
        klass="safety",
        verifier="deterministic",
        cover="scenario,question,choices,image_prompt",
        repair_hint="Remove every word that came from the drawing's text; write the scene from the hero's visuals only.",
    ),
    C(
        id="story_safe_text",
        scope="scene",
        title="Every page is safe and kind",
        plain="Every page was checked for anything scary, unkind or unsafe before you could see it.",
        klass="safety",
        verifier="both",
        rubric=SAFE_RUBRIC,
        cover="scenario,question,choices,image_prompt",
        repair_hint="Rewrite the page so it is gentle and kind, with no violence, fear, insults or danger.",
    ),
    C(
        id="schema_valid",
        scope="story",
        title="Eight complete pages",
        plain="The story has exactly eight complete pages.",
        klass="quality",
        verifier="deterministic",
        cover="scenario,question,choices,image_prompt",
        repair_hint="Provide all eight pages with every field filled.",
    ),
    C(
        id="one_correct_choice",
        scope="scene",
        title="Exactly one right answer",
        plain="Every question has exactly one right answer.",
        klass="quality",
        verifier="deterministic",
        cover="choices",
        repair_hint="Make exactly one of the two choices correct.",
    ),
    C(
        id="correct_choice_position_balanced",
        scope="story",
        title="The right answer moves around",
        plain="The right answer is not always the first button.",
        klass="quality",
        verifier="deterministic",
        cover="choices",
    ),
    C(
        id="character_named_in_scene",
        scope="scene",
        title="The hero is named on every page",
        plain="The hero's name is on every page.",
        klass="quality",
        verifier="deterministic",
        cover="scenario,question",
        repair_hint="Use the hero's name in both the scenario and the question.",
    ),
    C(
        id="visual_trait_referenced",
        scope="scene",
        title="The hero looks like the drawing",
        plain="Each page mentions something the hero really looks like in the drawing.",
        klass="quality",
        verifier="deterministic",
        cover="scenario,image_prompt",
        repair_hint="Mention one of the hero's visual traits in the scenario or the image prompt.",
    ),
    C(
        id="age_reading_level",
        scope="scene",
        title="Simple words for the child's age",
        plain="Sentences are short and the words are easy for this age.",
        klass="quality",
        verifier="deterministic",
        cover="scenario,question",
        repair_hint="Use at most two short sentences and simple, everyday words.",
    ),
    C(
        id="lesson_concept_in_scene",
        scope="scene",
        title="The lesson is on every page",
        plain="Every page is about the lesson, not just some pages.",
        klass="quality",
        verifier="both",
        rubric=CONCEPT_RUBRIC,
        cover="scenario,question,choices",
        repair_hint="Show the lesson through what the hero does or chooses on this page.",
    ),
    C(
        id="correct_choice_teaches_lesson",
        scope="scene",
        title="The right answer teaches the lesson",
        plain="The right answer is the one that shows the lesson.",
        klass="quality",
        verifier="judge",
        rubric=TEACHES_RUBRIC,
        cover="choices",
        repair_hint="Make the correct choice clearly embody the lesson and the other choice clearly not.",
    ),
    C(
        id="lesson_alignment",
        scope="story",
        title="The whole story teaches the lesson",
        plain="The whole story teaches the chosen lesson.",
        klass="quality",
        verifier="judge",
        rubric=LESSON_ALIGN_RUBRIC,
        pass_score=0.7,
        cover="scenario,question,choices",
    ),
    C(
        id="no_repeated_scenario",
        scope="story",
        title="No page repeats another",
        plain="No two pages tell the same moment.",
        klass="quality",
        verifier="deterministic",
        cover="scenario",
        repair_hint="Write a new moment with a different setting and event.",
    ),
    C(
        id="card_traits_checkable",
        scope="run",
        title="The hero has checkable features",
        plain="The hero was described by at least three things you can see.",
        klass="quality",
        verifier="deterministic",
        cover="character_card",
    ),
    C(
        id="original_character_only",
        scope="run",
        title="The hero is original",
        plain="The hero is not a famous cartoon or film character.",
        klass="quality",
        verifier="both",
        rubric=ORIGINAL_RUBRIC,
        cover="character_card",
    ),
    C(
        id="trait_in_image_prompt",
        scope="image",
        title="Pictures are asked to show the hero",
        plain="Each picture was asked to show the hero as drawn.",
        klass="quality",
        verifier="deterministic",
        cover="image_prompt",
        repair_hint="Add the hero's name and a visual trait to the image prompt.",
    ),
    C(
        id="illustration_present",
        scope="image",
        title="Every page has a picture",
        plain="Every page has a picture, or the story says plainly that one is missing.",
        klass="quality",
        verifier="deterministic",
        cover="image",
    ),
    C(
        id="image_matches_card",
        scope="image",
        title="The picture matches the hero",
        plain="Pictures look like the same hero.",
        klass="quality",
        verifier="judge",
        rubric=IMAGE_RUBRIC,
        pass_score=0.8,
        cover="image",
    ),
    C(
        id="image_no_text",
        scope="image",
        title="Pictures contain no words",
        plain="Pictures have no stray or garbled words painted into them.",
        klass="quality",
        verifier="judge",
        rubric=IMAGE_TEXT_RUBRIC,
        pass_score=0.8,
        cover="image",
        repair_hint="Paint the picture again with no words, letters or captions in it.",
    ),
    C(
        id="narration_present",
        scope="audio",
        title="Every page can be read aloud",
        plain="Every page can be read aloud, or the story says plainly that it cannot.",
        klass="quality",
        verifier="deterministic",
        cover="audio",
    ),
]

DET: dict[str, Callable] = {
    "no_drawing_text_obedience": d.no_drawing_text_obedience_scene,
    "story_safe_text": d.story_safe_text,
    "schema_valid": d.schema_valid,
    "one_correct_choice": d.one_correct_choice,
    "correct_choice_position_balanced": d.correct_choice_position_balanced,
    "character_named_in_scene": d.character_named_in_scene,
    "visual_trait_referenced": d.visual_trait_referenced,
    "age_reading_level": d.age_reading_level,
    "lesson_concept_in_scene": d.lesson_concept_in_scene,
    "no_repeated_scenario": d.no_repeated_scenario,
    "card_traits_checkable": d.card_traits_checkable,
    "original_character_only": d.original_character_only,
    "trait_in_image_prompt": d.trait_in_image_prompt,
    "illustration_present": d.illustration_present,
    "narration_present": d.narration_present,
}

CORE_IDS = {c.id for c in CORE}
MAX_ADDED = 4


def oath_hash(commitments: list[Commitment]) -> str:
    blob = json.dumps(
        [c.model_dump() for c in sorted(commitments, key=lambda c: c.id)], sort_keys=True, ensure_ascii=False
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def core_oath() -> Oath:
    cs = [c.model_copy(deep=True) for c in CORE]
    for c in cs:
        if c.pass_score is None and c.id == "lesson_alignment":
            c.pass_score = get_settings().thresholds.lesson_alignment_pass
        if c.id == "image_matches_card":
            c.pass_score = get_settings().thresholds.image_match_pass
    return Oath(commitments=cs, hash=oath_hash(cs))


def merge_additions(base: Oath, additions: list[dict]) -> tuple[Oath, list[str]]:
    """Add lesson-specific promises. The core can never be removed, replaced or relaxed. Returns (oath, rejections)."""
    rejected: list[str] = []
    cs = [c.model_copy(deep=True) for c in base.commitments]
    have = {c.id for c in cs}
    added = 0
    for raw in additions:
        try:
            cid = str(raw.get("id", "")).strip().lower().replace(" ", "_")
            if not cid.startswith("lesson_specific_"):
                cid = "lesson_specific_" + cid.removeprefix("lesson_")
            if cid in have or cid in CORE_IDS:
                rejected.append(f"{cid}: id already used")
                continue
            scope = raw.get("scope", "scene")
            rubric = str(raw.get("rubric", "")).strip()
            if scope not in ("scene", "story") or len(rubric) < 20:
                rejected.append(f"{cid}: needs scope scene/story and a rubric")
                continue
            if added >= MAX_ADDED:
                rejected.append(f"{cid}: more than {MAX_ADDED} additions")
                continue
            cs.append(
                C(
                    id=cid, scope=scope, core=False, klass="quality", verifier="judge",
                    title=str(raw.get("title", cid))[:80], plain=str(raw.get("plain", raw.get("title", cid)))[:160],
                    rubric=rubric[:600], cover="scenario,question,choices",
                    repair_hint=str(raw.get("repair_hint", ""))[:200],
                )
            )  # fmt: skip
            have.add(cid)
            added += 1
        except Exception as e:  # a malformed addition is dropped, never fatal
            rejected.append(f"malformed addition: {e}")
    return Oath(commitments=cs, hash=oath_hash(cs)), rejected
