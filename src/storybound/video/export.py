"""Make the read-along video of a finished story that lives in a run folder (used by the API)."""

from __future__ import annotations

from pathlib import Path

from . import agent, story


def make_for_run(run_dir: Path) -> dict:
    """Build `<run_dir>/video/video.mp4` from the story package. Returns the receipt (outcome, broken, video)."""
    return agent.make(story.build_spec(run_dir, own_media=True), title=run_dir.name, out=run_dir / "video", max_repairs=1)
