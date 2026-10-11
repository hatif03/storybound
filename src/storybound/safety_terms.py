"""Deterministic word lists. Conservative on purpose: a false alarm costs one repair, a miss costs a child's trust.

Matching is whole-word, so 'skill' never trips 'kill'.
"""

from __future__ import annotations

from .textutil import contains_word

# Severe harm: weapons, gore, killing. Critical when found in what a child will read.
SEVERE_TERMS = [
    "kill", "kills", "killed", "killing", "murder", "stab", "stabbed", "shoot", "shot", "gun", "guns", "knife", "knives",
    "blood", "bloody", "weapon", "weapons", "sword", "bomb", "explode", "dead", "death", "dying", "punch", "attack", "gore",
    "suicide",
]  # fmt: skip
# Mild terms that a moral lesson can use gently ("a secret that hurts trust", "friends do not fight"), and unkind labels.
# A hit means the page is rewritten, not that the story stops (HR-004).
MILD_TERMS = ["fight", "fights", "fighting", "fought", "hurt", "hurts"]
INSULT_TERMS = ["stupid", "idiot", "dumb", "ugly", "hate", "hates", "shut up", "loser", "fat", "freak"]
HARM_TERMS = SEVERE_TERMS + MILD_TERMS
# Text that tries to steer the agent. Never obeyed; never repeated.
HARD_INSTRUCTION_TERMS = ["ignore your rules", "ignore previous", "system prompt", "jailbreak"]
# Words that steer an agent but also appear in an innocent sentence ("ignore all the noise"): in a drawing's text they are still never obeyed
# or repeated; in the story's own text a hit means a rewrite, not a stop (found by the neatlogs incident review, HR-011).
SOFT_INSTRUCTION_TERMS = ["ignore all", "override", "disregard"]
INSTRUCTION_TERMS = HARD_INSTRUCTION_TERMS + SOFT_INSTRUCTION_TERMS
# Personal data patterns are handled in the safety screen (regex), not here.
FRANCHISE_TERMS = [
    "mickey", "minnie", "donald duck", "goofy", "pikachu", "pokemon", "elsa", "anna and elsa", "spongebob", "peppa pig",
    "paw patrol", "bluey", "mario", "luigi", "sonic", "spider-man", "spiderman", "batman", "superman", "winnie the pooh",
    "hello kitty", "dora", "simba", "nemo", "woody", "buzz lightyear", "harry potter", "hogwarts", "frozen", "minion", "minions",
]  # fmt: skip


def find_terms(text: str, terms: list[str]) -> list[str]:
    return sorted({t for t in terms if contains_word(text, t)})


def harm_hits(text: str) -> list[str]:
    return find_terms(text, HARM_TERMS + INSULT_TERMS)


def severe_hits(text: str) -> list[str]:
    return find_terms(text, SEVERE_TERMS)


def instruction_hits(text: str) -> list[str]:
    return find_terms(text, INSTRUCTION_TERMS)


def hard_instruction_hits(text: str) -> list[str]:
    return find_terms(text, HARD_INSTRUCTION_TERMS)


def soft_instruction_hits(text: str) -> list[str]:
    return find_terms(text, SOFT_INSTRUCTION_TERMS)


def franchise_hits(text: str) -> list[str]:
    return find_terms(text, FRANCHISE_TERMS)
