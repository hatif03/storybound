"""One place for model ids, thresholds, budgets and environment. Swap a model here, nowhere else."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


# The default split of work between Vertex (Gemini) and the hackathon gateway, chosen on 11 Oct by holdout runs (HR-012): the planner on Nova 2 Lite and the
# quiz maker on Claude Haiku (text only, independent of the writer), the "no words in the picture" check on Claude Haiku. The writer, the oath author,
# the character card and the safety screen stay on Gemini: moving them lost quality (writer: 3 of 10 stories shipped a break; character card: Haiku
# read a drawn carrot as an ice-cream cone; safety screen: 23 of 26 fixtures). STORYBOUND_ROUTES= (empty) turns all routing off; without a gateway key
# every role falls back to Gemini.
DEFAULT_ROUTES = "story_planner=nova-2-lite,quiz_maker=claude-haiku,quiz_repair=claude-haiku"


def _parse_routes(raw: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for part in raw.split(","):
        if "=" in part:
            k, v = part.split("=", 1)
            if k.strip() and v.strip():
                out[k.strip()] = v.strip()
    return out


class Models(BaseModel):
    writer: str = "gemini-3.7-flash"
    vision: str = "gemini-3.7-flash"
    reserve: str = "gemini-3.1-pro-preview"
    image: str = "gemini-3.1-flash-image"
    image_fallback: str = "gemini-2.5-flash-image"
    tts: str = "gemini-2.5-flash-tts"
    tts_voice: str = "Kore"
    judge: str = os.environ.get("STORYBOUND_JUDGE_MODEL", "IFM/K2-Horizon-375B-A23B")
    # Which model each agent role uses when it is not the default. "role=model,role=model" in STORYBOUND_ROUTES, for example
    # "safety_screen=claude-haiku,story_planner=nova-2-lite". A role is matched by the part of its span name before the first dot
    # (scene_writer.3 -> scene_writer). Models starting with claude or nova go through the hackathon gateway (clients/gateway.py).
    routes: dict[str, str] = Field(default_factory=lambda: _parse_routes(os.environ.get("STORYBOUND_ROUTES", DEFAULT_ROUTES)))
    vision_judge: str = os.environ.get("STORYBOUND_VISION_JUDGE", "claude-haiku")  # who judges the pictures named in vision_judge_for; empty = the vision model (the painter's family)
    vision_judge_for: tuple[str, ...] = ("image_no_text",)
    judge_ensemble: str = os.environ.get("STORYBOUND_JUDGE_ENSEMBLE", "")  # a second judge from another family; the stricter verdict wins (experiment X3)

    def route(self, role: str) -> str | None:
        return self.routes.get(role) or self.routes.get(role.split(".")[0])


class Thresholds(BaseModel):
    lesson_alignment_pass: float = 0.7
    image_match_pass: float = 0.8
    lesson_drift_detect: float = 0.6
    image_drift_detect: float = 0.7
    max_repair_attempts: int = int(os.environ.get("STORYBOUND_MAX_REPAIRS", "2"))  # experiments X5 and X6 change it
    pages: int = 8
    max_correct_slot_share: int = 5  # same slot for at most this many of the 8 pages


class Sampling(BaseModel):
    """Judge sampling per commitment class. Safety is always 1.0 and cannot be lowered."""

    safety: float = 1.0
    quality: float = 0.5
    image: float = 0.5


class Budget(BaseModel):
    usd_per_story: float = 1.5
    pictures_usd_per_story: float = 0.16  # what the agent may spend on pictures when it chooses the pages itself (four at the list price)
    seconds_per_story: float = 240.0


class Prices(BaseModel):
    """ESTIMATES, labelled as such everywhere they are shown. neatlogs holds the measured figure; cfo.ai gets that one."""

    gemini_in_per_m: float = 0.50
    gemini_out_per_m: float = 3.00
    k2_per_m: float = 0.0  # no price known
    image_each: float = 0.04
    tts_each: float = 0.002
    gemini_models: dict[str, tuple[float, float]] = Field(default_factory=lambda: {"gemini-3.1-pro-preview": (1.25, 10.0)})  # ASSUMED list price of the reserve (Pro) model, USD per million tokens (in, out): not read from a bill
    # Gateway models, USD per million tokens (input, output), read from the gateway's /model/info on 11 Oct (they include its markup).
    gateway: dict[str, tuple[float, float]] = Field(default_factory=lambda: {
        "claude-haiku": (1.1, 5.5), "claude-sonnet-4.6": (3.3, 16.5), "claude-opus-4.6": (5.5, 27.5),
        "nova-micro": (0.035, 0.14), "nova-lite": (0.06, 0.24), "nova-pro": (0.8, 3.2), "nova-2-lite": (0.33, 2.75),
    })  # fmt: skip


class Settings(BaseModel):
    models: Models = Field(default_factory=Models)
    thresholds: Thresholds = Field(default_factory=Thresholds)
    sampling: Sampling = Field(default_factory=Sampling)
    budget: Budget = Field(default_factory=Budget)
    prices: Prices = Field(default_factory=Prices)

    gcp_project: str = "project-f0b6b4ce-541f-43ff-9f7"
    gcp_location: str = "global"
    ifm_base_url: str = "https://api.ifm.ai/v1"
    request_timeout_s: float = 90.0  # images
    text_timeout_s: float = float(os.environ.get("STORYBOUND_TEXT_TIMEOUT_S", "90"))  # HR-005: 40 s was tried and not kept
    judge_timeout_s: float = 180.0
    judge_max_tokens: int = 4096
    hedge_after_s: float = float(os.environ.get("STORYBOUND_HEDGE_S", "45"))  # HR-011: send a stalled text call a second time after this many seconds; 0 = off
    thinking_headroom: int = 2048  # Gemini 3 thinking tokens count against max_output_tokens


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    s.gcp_project = os.getenv("GCP_PROJECT", s.gcp_project)
    s.gcp_location = os.getenv("GCP_LOCATION", s.gcp_location)
    s.ifm_base_url = os.getenv("IFM_BASE_URL", s.ifm_base_url)
    return s


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default)
