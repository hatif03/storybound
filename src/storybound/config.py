"""One place for model ids, thresholds, budgets and environment. Swap a model here, nowhere else."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


class Models(BaseModel):
    writer: str = "gemini-3.7-flash"
    vision: str = "gemini-3.7-flash"
    reserve: str = "gemini-3.1-pro-preview"
    image: str = "gemini-3.1-flash-image"
    image_fallback: str = "gemini-2.5-flash-image"
    tts: str = "gemini-2.5-flash-tts"
    tts_voice: str = "Kore"
    judge: str = "IFM/K2-Horizon-375B-A23B"


class Thresholds(BaseModel):
    lesson_alignment_pass: float = 0.7
    image_match_pass: float = 0.8
    lesson_drift_detect: float = 0.6
    image_drift_detect: float = 0.7
    max_repair_attempts: int = 2
    pages: int = 8
    max_correct_slot_share: int = 5  # same slot for at most this many of the 8 pages


class Sampling(BaseModel):
    """Judge sampling per commitment class. Safety is always 1.0 and cannot be lowered."""

    safety: float = 1.0
    quality: float = 0.5
    image: float = 0.5


class Budget(BaseModel):
    usd_per_story: float = 1.5
    seconds_per_story: float = 240.0


class Settings(BaseModel):
    models: Models = Field(default_factory=Models)
    thresholds: Thresholds = Field(default_factory=Thresholds)
    sampling: Sampling = Field(default_factory=Sampling)
    budget: Budget = Field(default_factory=Budget)

    gcp_project: str = "project-f0b6b4ce-541f-43ff-9f7"
    gcp_location: str = "global"
    ifm_base_url: str = "https://api.ifm.ai/v1"
    request_timeout_s: float = 90.0
    judge_timeout_s: float = 180.0
    judge_max_tokens: int = 4096


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    s.gcp_project = os.getenv("GCP_PROJECT", s.gcp_project)
    s.gcp_location = os.getenv("GCP_LOCATION", s.gcp_location)
    s.ifm_base_url = os.getenv("IFM_BASE_URL", s.ifm_base_url)
    return s


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default)
