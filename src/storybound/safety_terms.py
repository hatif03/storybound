"""Deterministic word lists. Conservative on purpose: a false alarm costs one repair, a miss costs a child's trust.

Matching is whole-word, so 'skill' never trips 'kill'.
"""

from __future__ import annotations

from .textutil import contains_word

# Harm to people or animals, weapons, gore, cruelty. Critical when found in what a child will read.
HARM_TERMS = [
    "kill", "kills", "killed", "killing", "murder", "stab", "stabbed", "shoot", "shot", "gun", "guns", "knife", "knives",
    "blood", "bloody", "weapon", "weapons", "sword", "bomb", "explode", "dead", "death", "dying",
    "fight", "fights", "fighting", "fought", "punch", "hurt", "hurts", "attack", "gore", "suicide",
]  # fmt: skip
# Name-calling and unkind labels, which are not allowed in a story that teaches kindness.
INSULT_TERMS = ["stupid", "idiot", "dumb", "ugly", "hate", "hates", "shut up", "loser", "fat", "freak"]
# Text that tries to steer the agent. Never obeyed; never repeated.
INSTRUCTION_TERMS = [
    "ignore your rules",
    "ignore previous",
    "ignore all",
    "system prompt",
    "override",
    "jailbreak",
    "disregard",
]
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


def instruction_hits(text: str) -> list[str]:
    return find_terms(text, INSTRUCTION_TERMS)


def franchise_hits(text: str) -> list[str]:
    return find_terms(text, FRANCHISE_TERMS)
