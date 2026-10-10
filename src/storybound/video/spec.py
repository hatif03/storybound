"""The video spec: scenes of typed blocks. Numbers on screen are `Claim` references, never typed values."""

from __future__ import annotations

import hashlib
import json
from typing import Literal

from pydantic import BaseModel, Field

BLOCK_TYPES = ("title", "text", "claim", "bars", "list", "image", "choices")


class Claim(BaseModel):
    id: str
    label: str
    refs: list[str]  # "report:<sweep name>#dotted.path" or "file:<repo path>#dotted.path"
    fmt: str = "{0}"  # on-screen text, str.format over the resolved values
    spoken: str | None = None  # narration text, same placeholders
    ratio: bool = False  # bars draw refs[0] / refs[1]


class Block(BaseModel):
    type: Literal["title", "text", "claim", "bars", "list", "image", "choices"]
    text: str = ""
    claim: str | None = None  # claim id (type "claim")
    items: list[dict | str] = Field(default_factory=list)  # bars: {label, claim, tone}; list: strings; choices: {text, state}
    at_frac: float | None = None  # appear this far (0-1) through the narration instead of in order
    src: str = ""  # image path, repo relative, only under assets/


class Scene(BaseModel):
    id: str
    narration: str  # may hold {claim_id} placeholders, resolved to the spoken form
    blocks: list[Block]
    covers: list[str] = Field(default_factory=list)  # "neatlogs:architecture" and so on
    mood: str = "happy-flap"  # which Pip the owl pose to show: happy-flap, wink, dizzy-confused, cool-sunglasses, heart-eyes, party-cupcake, shy-giggle
    min_seconds: float = 4.0
    pause: float = 0.8  # silence after the narration, for a child to think
    layout: Literal["stack", "split"] = "stack"  # split: the first image on the left, the rest on the right
    foot: bool = True  # the "#neatHack" footer; off for videos a child will watch
    kind: Literal["claim", "story"] = "claim"  # story: text comes from an already verified story, not from us


class Spec(BaseModel):
    title: str
    claims: list[Claim]
    scenes: list[Scene]
    max_seconds: float = 180.0
    narration_style: str | None = None
    requires_coverage: bool = False  # the 3 minute demo must cover each tool on the five points

    def claim(self, cid: str) -> Claim:
        for c in self.claims:
            if c.id == cid:
                return c
        raise KeyError(f"unknown claim '{cid}'")

    def digest(self) -> str:
        return hashlib.sha256(json.dumps(self.model_dump(), sort_keys=True).encode()).hexdigest()[:16]


def load(path: str) -> Spec:
    return Spec.model_validate_json(open(path, encoding="utf-8").read())
