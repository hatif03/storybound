"""Vision agent: the drawing becomes a character card (name, species, checkable visual traits, palette)."""

from __future__ import annotations

import re

from .. import prompts
from ..media import Drawing
from ..models import CharacterCard
from ..safety_terms import franchise_hits, harm_hits
from .common import ask_json, rng

_NAME_OK = re.compile(r"^[A-Za-z][A-Za-z' -]{0,23}$")


def clean_hero_name(raw: str | None) -> str | None:
    """A hero name typed by a grown-up: letters only, short, nothing blocked. Anything else is ignored."""
    if not raw:
        return None
    name = " ".join(raw.split())
    if not _NAME_OK.match(name) or harm_hits(name) or franchise_hits(name):
        return None
    return name


def build_card(drawing: Drawing, hero_name: str | None = None, seed: str = "1") -> tuple[CharacterCard, dict]:
    letter = rng(seed, "name").choice("ABCDEFGHJKLMNOPRSTWZ")
    rule = (
        f'use exactly this name: "{hero_name}"'
        if hero_name
        else f"invent a short, friendly, original first name that starts with the letter {letter} (never Pip: that is the owl guide)"
    )
    user = prompts.CHARACTER_USER.replace("{hero_name_rule}", rule)
    r = ask_json(
        "character_card",
        prompts.CHARACTER_SYSTEM,
        user,
        images=[(drawing.data, drawing.mime)],
        temperature=0.5,
        max_tokens=800,
    )
    j = r.value if isinstance(r.value, dict) else {}
    traits = [str(t).strip() for t in j.get("traits", []) if str(t).strip()][:6]
    name = clean_hero_name(hero_name) or clean_hero_name(str(j.get("name", ""))) or "Pip"
    card = CharacterCard(
        name=name,
        species=str(j.get("species", "friend"))[:40],
        traits=traits,
        palette=[str(c) for c in j.get("palette", [])][:4],
        one_line=str(j.get("one_line", ""))[:200],
    )
    return card, {"tokens_in": r.usage.input_tokens, "tokens_out": r.usage.output_tokens}
