"""Deterministic verifiers. They decide first, cost nothing and never hallucinate.

Each takes (subject, ctx) and returns a Det. `ctx` is a Ctx (character card, lesson, age, ignored drawing text, story so far).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..lessons import Lesson
from ..models import CharacterCard, Page, Status
from ..safety_terms import franchise_hits, harm_hits, instruction_hits, severe_hits
from ..textutil import contains_word, content_words, jaccard, sentences, stem_hit, words


@dataclass
class Ctx:
    card: CharacterCard | None = None
    lesson: Lesson | None = None
    age: int = 6
    ignored_text: list[str] = field(default_factory=list)
    pages: list[Page] = field(default_factory=list)  # the story so far (accepted pages)
    pages_total: int = 8
    max_correct_slot_share: int = 5
    seed: str = "0"


@dataclass
class Det:
    status: Status
    actual: str = ""
    matched: str | None = None
    quote: str | None = None
    scene: int | None = None
    extra: dict = field(default_factory=dict)


def _ok(actual: str = "") -> Det:
    return Det("pass", actual)


def _bad(actual: str, status: Status = "violation", **kw) -> Det:
    return Det(status, actual, **kw)


# ---- scene scope -----------------------------------------------------------------------------------------------------


def one_correct_choice(p: Page, ctx: Ctx) -> Det:
    n = sum(1 for c in p.choices if c.is_correct)
    if len(p.choices) != 2:
        return _bad(f"{len(p.choices)} choices, expected 2", scene=p.index)
    return _ok(f"{n} correct") if n == 1 else _bad(f"{n} correct choices, expected exactly 1", scene=p.index)


def character_named_in_scene(p: Page, ctx: Ctx) -> Det:
    name = ctx.card.name if ctx.card else ""
    if not name:
        return Det("verification_error", "no character name in context")
    missing = [f for f, t in (("scenario", p.scenario), ("question", p.question)) if not contains_word(t, name)]
    if missing:
        return _bad(f"'{name}' missing from {' and '.join(missing)}", scene=p.index)
    return Det("pass", f"'{name}' present", matched=name, scene=p.index)


def visual_trait_referenced(p: Page, ctx: Ctx) -> Det:
    if not ctx.card:
        return Det("verification_error", "no character card in context")
    text = p.scenario + " " + p.image_prompt
    for trait in ctx.card.traits:
        keys = [w for w in words(trait) if w not in {"with", "and", "has", "have", "wearing"} and len(w) > 3]
        for k in keys:
            if stem_hit(text, k):
                return Det("pass", f"trait word '{k}' found", matched=k, scene=p.index)
    return _bad("no visual trait of the hero appears in the scenario or image prompt", scene=p.index)


_MAX_SENT_WORDS = {4: 10, 5: 12, 6: 14, 7: 16, 8: 18}


def max_sentence_words(age: int) -> int:
    return _MAX_SENT_WORDS.get(age, 14)


def target_sentence_words(age: int) -> int:
    """What the page writer is told: two words under the limit, because a stated limit becomes the writer's target (HR-003)."""
    return max(max_sentence_words(age) - 2, 6)


def age_reading_level(p: Page, ctx: Ctx) -> Det:
    limit = max_sentence_words(ctx.age)
    sents = sentences(p.scenario)
    if len(sents) > 2:
        return _bad(f"{len(sents)} sentences in the scenario, at most 2 allowed", scene=p.index)
    longest = max((len(words(s)) for s in sents), default=0)
    if longest > limit:
        return _bad(f"a sentence has {longest} words; the limit for age {ctx.age} is {limit}", scene=p.index)
    ws = words(p.scenario + " " + p.question)
    hard = [part for w in ws for part in w.split("-") if len(part) > 10]  # "peach-colored" is two easy words
    if ws and len(hard) / len(ws) > 0.06:
        return _bad(f"too many long words: {', '.join(sorted(set(hard))[:4])}", scene=p.index)
    return Det("pass", f"{len(sents)} sentences, longest {longest} words", scene=p.index)


def lesson_concept_in_scene(p: Page, ctx: Ctx) -> Det:
    if not ctx.lesson:
        return Det("verification_error", "no lesson in context")
    text = p.all_text()
    for t in ctx.lesson.terms:
        if contains_word(text, t) or (" " not in t and stem_hit(text, t)):
            return Det("pass", f"lesson term '{t}' found", matched=t, scene=p.index)
    return _bad(f"none of the {ctx.lesson.title.lower()} terms appear in this page", scene=p.index)


def story_safe_text(p: Page, ctx: Ctx) -> Det:
    text = p.review_text()
    grave = severe_hits(text) + instruction_hits(text) + find_pii(text)
    if grave:
        return _bad(f"unsafe terms: {', '.join(sorted(set(grave)))}", "critical", matched=grave[0], scene=p.index)
    mild = harm_hits(text)
    if mild:  # a rewrite, not a stop: "a secret that hurts trust" is a lesson, not violence (HR-004)
        return _bad(f"unkind or harsh terms: {', '.join(sorted(set(mild)))}", matched=mild[0], scene=p.index)
    return Det("pass", "no blocked terms", scene=p.index)


def no_drawing_text_obedience_scene(p: Page, ctx: Ctx) -> Det:
    return no_drawing_text_obedience([p], ctx)


# ---- story / run scope -----------------------------------------------------------------------------------------------


def schema_valid(pages: list[Page], ctx: Ctx) -> Det:
    n = ctx.pages_total
    if [p.index for p in pages] != list(range(1, n + 1)):
        return _bad(f"pages numbered {[p.index for p in pages]}, expected 1..{n}")
    for p in pages:
        if not (p.scenario.strip() and p.question.strip() and p.image_prompt.strip()):
            return _bad("empty scenario, question or image prompt", scene=p.index)
        if any(not (c.text.strip() and c.feedback.strip()) for c in p.choices):
            return _bad("a choice has empty text or feedback", scene=p.index)
    return _ok(f"{n} pages, all fields present")


def correct_choice_position_balanced(pages: list[Page], ctx: Ctx) -> Det:
    slots = [next((i for i, c in enumerate(p.choices) if c.is_correct), -1) for p in pages]
    worst = max((slots.count(s) for s in set(slots)), default=0)
    if worst > ctx.max_correct_slot_share:
        return _bad(f"the correct answer is in the same slot on {worst} of {len(pages)} pages")
    return _ok(f"slots {slots}")


def no_repeated_scenario(pages: list[Page], ctx: Ctx) -> Det:
    sets = [content_words(p.scenario) for p in pages]
    for j in range(1, len(sets)):
        for i in range(j):
            sim = jaccard(sets[i], sets[j])
            if sim > 0.6:
                return _bad(
                    f"page {pages[j].index} repeats page {pages[i].index} (similarity {sim:.2f})", scene=pages[j].index
                )
    return _ok("no repeated scenarios")


def _harmful_tokens(ignored: list[str]) -> list[str]:
    toks: list[str] = []
    for s in ignored:
        toks += harm_hits(s) + instruction_hits(s)
        toks += [w for w in words(s) if w in {"ignore", "disregard", "override", "jailbreak"}]
    return sorted(set(toks))


def no_drawing_text_obedience(pages: list[Page], ctx: Ctx) -> Det:
    """Harmful or instruction-like words found in the drawing must not appear anywhere the child reads or sees."""
    if not ctx.ignored_text:
        return Det("pass", "no text in the drawing")
    bad = _harmful_tokens(ctx.ignored_text)
    for p in pages:
        text = p.review_text()
        for phrase in ctx.ignored_text:
            if len(phrase) > 3 and phrase.lower() in text.lower():
                return _bad(
                    f"the drawing's text '{phrase}' was copied into the story",
                    "critical",
                    matched=phrase,
                    scene=p.index,
                )
        for t in bad:
            if contains_word(text, t):
                return _bad(f"'{t}' from the drawing's text appears in the story", "critical", matched=t, scene=p.index)
    return Det("pass", f"ignored {len(ctx.ignored_text)} text item(s); none reached the story")


def card_traits_checkable(card: CharacterCard, ctx: Ctx) -> Det:
    good = [t for t in card.traits if len(words(t)) >= 1 and len(t.strip()) >= 3]
    if len(good) < 3:
        return _bad(f"{len(good)} concrete traits, at least 3 needed")
    return _ok(f"{len(good)} traits")


def original_character_only(card: CharacterCard, ctx: Ctx) -> Det:
    blob = " ".join([card.name, card.species, card.one_line, *card.traits])
    hits = franchise_hits(blob)
    if hits:
        return _bad(f"resembles an existing character: {', '.join(hits)}", matched=hits[0])
    return _ok("no franchise names")


# ---- media -----------------------------------------------------------------------------------------------------------

_MAGIC = (b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff", b"RIFF")


def illustration_present(data: bytes | None, ctx: Ctx) -> Det:
    if not data:
        return _bad("no image bytes returned")
    if len(data) < 4_000:
        return _bad(f"image too small ({len(data)} bytes)")
    if not any(data.startswith(m) for m in _MAGIC):
        return _bad("not a PNG, JPEG or WebP image")
    return _ok(f"{len(data)} bytes")


def narration_present(data: bytes | None, ctx: Ctx, text: str = "") -> Det:
    if not data:
        return _bad("no audio bytes returned")
    if len(data) < 1_500:
        return _bad(f"audio too small ({len(data)} bytes)")
    if not (data[:3] == b"ID3" or data[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2") or data[:4] == b"RIFF"):
        return _bad("not an MP3 or WAV file")
    if text:
        expect = len(words(text)) / 2.4  # about 2.4 words per second, read slowly
        est = len(data) * 8 / 48_000  # MP3 at about 48 kbit/s; rough on purpose
        if est < expect * 0.3:
            return _bad(f"audio is about {est:.1f}s for text that needs about {expect:.1f}s")
    return _ok(f"{len(data)} bytes")


def trait_in_image_prompt(p: Page, ctx: Ctx) -> Det:
    if not ctx.card:
        return Det("verification_error", "no character card in context")
    text = p.image_prompt
    if contains_word(text, ctx.card.name) or any(
        stem_hit(text, k) for t in ctx.card.traits for k in words(t) if len(k) > 3
    ):
        return _ok("hero trait present in the image prompt")
    return _bad("the image prompt does not mention the hero or a trait", scene=p.index)


_PII = [
    (re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b"), "phone number"),
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"), "email address"),
    (re.compile(r"\b\d{1,5}\s+\w+\s+(street|st|road|rd|avenue|ave|lane|ln)\b", re.I), "street address"),
]


def find_pii(text: str) -> list[str]:
    return [label for rx, label in _PII if rx.search(text)]
