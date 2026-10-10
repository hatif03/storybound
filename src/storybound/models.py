"""Shared data shapes: the story, the character card, and the one verdict object used everywhere."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Status = Literal["pass", "warning", "violation", "critical", "skipped", "verification_error"]
Scope = Literal["run", "story", "scene", "image", "audio"]
VerdictBy = Literal["deterministic", "judge", "both", "none"]


class Choice(BaseModel):
    id: str
    text: str
    feedback: str
    is_correct: bool


class Page(BaseModel):
    index: int
    scenario: str
    question: str
    choices: list[Choice]
    image_prompt: str
    narration_text: str = ""

    def all_text(self) -> str:
        parts = [self.scenario, self.question]
        for c in self.choices:
            parts += [c.text, c.feedback]
        return "\n".join(parts)

    def review_text(self) -> str:
        """Everything a child reads or hears, plus the image prompt (which becomes a picture)."""
        return self.all_text() + "\n" + self.image_prompt


class CharacterCard(BaseModel):
    name: str
    species: str
    traits: list[str]
    palette: list[str] = Field(default_factory=list)
    one_line: str = ""


class Lesson(BaseModel):
    id: str
    title: str
    blurb: str
    concept: str  # one plain sentence the story must teach
    terms: list[str]  # words that show the concept is present
    icon: str = ""


class Evidence(BaseModel):
    scene: int | None = None
    quote: str | None = None
    matched: str | None = None


class Verdict(BaseModel):
    commitment: str
    scope: str  # "run", "story", "scene 5", "image 5", "audio 5"
    status: Status = "skipped"
    verdict_by: VerdictBy = "none"
    det_status: Status | None = None
    judge_status: Status | None = None
    sampled: bool = False
    sample_seed: str | None = None
    judge_model: str | None = None
    score: float | None = None
    expected: str = ""
    actual: str = ""
    evidence: Evidence = Field(default_factory=Evidence)
    cover: str = ""
    attempt: int = 0
    reasoning: str = ""
    trace_id: str = ""

    @property
    def ok(self) -> bool:
        return self.status in ("pass", "warning", "skipped")


class Commitment(BaseModel):
    """One promise in the oath. `plain` is the parent-readable sentence."""

    id: str
    scope: Literal["run", "story", "scene", "image", "audio"]
    title: str
    plain: str
    core: bool = True
    klass: Literal["safety", "quality"] = "quality"
    verifier: Literal["deterministic", "judge", "both"] = "deterministic"
    rubric: str = ""  # for judged commitments: what the judge must decide
    pass_score: float | None = None
    repair_hint: str = ""
    cover: str = ""  # which output fields this commitment touches


class Oath(BaseModel):
    commitments: list[Commitment]
    hash: str = ""
