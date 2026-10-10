"""Story package (a drawing's finished, verified story with its media) -> a read-along video spec.

No planner: the content is the story. Numbers on the last card are claims read from the story's own receipt.
"""

from __future__ import annotations

import json
from pathlib import Path

from .claims import ROOT
from .spec import Block, Claim, Scene, Spec

STYLE = "Read warmly like a friendly storyteller to a young child, at a natural lively pace with gentle expression."
PAGE_MOODS = ["happy-flap", "wink", "shy-giggle", "cool-sunglasses"]


def _rel(p: Path) -> str:
    return p.resolve().relative_to(ROOT).as_posix()


def build_spec(story_dir: Path, *, own_media: bool = False) -> Spec:
    st = json.loads((story_dir / "story.json").read_text(encoding="utf-8"))
    base = _rel(story_dir)
    hero = st["card"]["name"]
    media = st.get("media", {})
    ref = f"file:{base}/story.json#receipt.counts"
    claims = [
        Claim(id="checks", label="checks were run on this story before it reached the child", refs=[f"{ref}.checks"]),
        Claim(id="repairs", label="pages were rewritten because they broke a promise", refs=[f"{ref}.repairs"]),
        Claim(id="promises", label="promises were written for this story before the first page", refs=[f"{ref}.commitments"]),
    ]
    traits = ", ".join(st["card"].get("traits", [])[:2])
    scenes = [Scene(
        id="intro", kind="story", layout="split", mood="happy-flap", pause=1.5,
        narration=f"This is {hero}, the hero of a story that began with a drawing. Let's read it together.",
        blocks=[Block(type="image", src=f"{base}/{st['drawing']}"), Block(type="title", text=f"Meet {hero}"),
                *([Block(type="text", text=traits.capitalize())] if traits else [])],
    )]
    for k, p in enumerate(st["pages"]):
        n = p["index"]
        img = media.get(f"image:{n}")
        pic = [Block(type="image", src=f"{base}/{img}")] if img else []
        right = next(c for c in p["choices"] if c["is_correct"])
        scenes.append(Scene(
            id=f"p{n}-read", kind="story", layout="split", mood=PAGE_MOODS[k % len(PAGE_MOODS)], pause=2.0,
            narration=f"{p['scenario']} {p['question']}",
            blocks=[*pic, Block(type="text", text=p["scenario"]),
                    Block(type="choices", at_frac=0.72, items=[{"text": c["text"], "state": "neutral"} for c in p["choices"]])],
        ))
        scenes.append(Scene(
            id=f"p{n}-answer", kind="story", layout="split", mood="heart-eyes", pause=0.9,
            narration=f"Yes! {right['feedback']}",
            blocks=[*pic, Block(type="choices", items=[{"text": c["text"], "state": "correct" if c["is_correct"] else "wrong"} for c in p["choices"]]),
                    Block(type="text", text=right["feedback"], at_frac=0.35)],
        ))
    scenes.append(Scene(
        id="end", mood="party-cupcake", pause=1.2, foot=False,
        narration="The end. Before this story reached you, a checker ran {checks} checks, and rewrote {repairs} pages to keep every promise.",
        blocks=[Block(type="title", text="The end"), Block(type="claim", claim="checks"), Block(type="claim", claim="repairs")],
    ))
    return Spec(title=f"{hero} read-along", claims=claims, scenes=scenes, narration_style=STYLE, max_seconds=300, own_media=own_media)
