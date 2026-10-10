"""Small text helpers shared by the verifiers: no model calls."""

from __future__ import annotations

import re

_WORD = re.compile(r"[A-Za-z][A-Za-z'\-]*")
_SENT = re.compile(r"(?<=[.!?])\s+")
STOP = frozenset(
    "a an the and or but of to in on at for with is are was were be been it its his her their they he she we you i "
    "this that these those as by from up down out so then than too very can could would will just not no yes".split()
)


def words(text: str) -> list[str]:
    return [w.lower() for w in _WORD.findall(text)]


def content_words(text: str) -> set[str]:
    return {w for w in words(text) if w not in STOP and len(w) > 2}


def sentences(text: str) -> list[str]:
    return [s for s in _SENT.split(text.strip()) if s.strip()]


def contains_word(text: str, term: str) -> bool:
    """Whole-word, case-insensitive match; multi-word terms match as a phrase."""
    return re.search(rf"(?<![A-Za-z]){re.escape(term)}(?![A-Za-z])", text, re.I) is not None


def stem_hit(text: str, term: str) -> bool:
    """Loose match so 'shares' and 'sharing' both count for 'share'."""
    stem = term.lower()[: max(4, len(term) - 2)] if len(term) > 4 else term.lower()
    return re.search(rf"(?<![A-Za-z]){re.escape(stem)}", text, re.I) is not None


def jaccard(a: set[str], b: set[str]) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


def norm_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()
