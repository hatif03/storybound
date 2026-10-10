"""Tolerant JSON extraction for model output (reasoning preambles, code fences, trailing prose)."""

from __future__ import annotations

import json
import re

from .errors import ParseError

_THINK = re.compile(r"<think>.*?</think>", re.S)
_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.S)


def extract_json(text: str) -> dict | list:
    if not text:
        raise ParseError("empty model output")
    t = _THINK.sub("", text).strip()
    m = _FENCE.search(t)
    if m:
        t = m.group(1).strip()
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        pass
    # last resort: the outermost balanced object or array
    for open_c, close_c in (("{", "}"), ("[", "]")):
        start = t.find(open_c)
        end = t.rfind(close_c)
        if start != -1 and end > start:
            try:
                return json.loads(t[start : end + 1])
            except json.JSONDecodeError:
                continue
    raise ParseError(f"no JSON found in model output: {t[:120]!r}")
