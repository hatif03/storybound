"""Drill: the painter writes words into a picture. Does the vision judge catch it, is the picture painted again, and does neatlogs' detection fire?

  python scripts/drill_picture_words.py [--name picture-words-drill] [--pictures 2]

The first painting of the first page is replaced by a picture with words painted in (the fixture bunny with a big caption drawn over it, made here);
every other painting is the real painter. Tagged `chaos` in neatlogs. Expected: a `verify:image_no_text` span with status violation, a
`scene.repair` event ("picture did not pass; painting it once more"), a second picture that passes, and a hit on the detection
"Picture has words painted in". Costs about $0.05 (a few pictures and checks).
"""

from __future__ import annotations

import argparse
import io
import sys
import threading
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from storybound import tracing  # noqa: E402

tracing.init()

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from storybound import media, pipeline  # noqa: E402
from storybound.clients import images as real_images  # noqa: E402
from storybound.clients.usage import Result  # noqa: E402
from storybound.events import EventLog  # noqa: E402

FIXTURE = ROOT / "assets" / "test-drawings" / "benign" / "bunny-bow-carrot.png"


def picture_with_words(src: bytes) -> bytes:
    """The fixture picture with large captions painted across it: what a painter that writes words into a scene produces."""
    im = Image.open(io.BytesIO(src)).convert("RGB").resize((768, 768))
    dr = ImageDraw.Draw(im)
    font = ImageFont.load_default(size=88)
    for y, text in ((40, "HAPPY BUNNY"), (330, "SHARE THE"), (620, "CARROT!")):
        dr.rectangle((20, y - 6, 748, y + 100), fill=(255, 255, 255))
        dr.text((40, y), text, fill=(200, 30, 30), font=font)
    out = io.BytesIO()
    im.save(out, "PNG")
    return out.getvalue()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="picture-words-drill")
    ap.add_argument("--save", help="write the picture with words here (a PNG)")
    a = ap.parse_args()

    src = FIXTURE.read_bytes()
    bad = picture_with_words(src)
    if a.save:
        Path(a.save).write_bytes(bad)
    calls = {"n": 0}
    lock = threading.Lock()
    original = real_images.illustrate

    def illustrate(prompt, *, reference=None):
        with lock:
            calls["n"] += 1
            first = calls["n"] == 1
        if first:
            return Result(value=bad, raw_text="image/png")
        return original(prompt, reference=reference)

    pipeline.images.illustrate = illustrate  # the first painting only; the repaint and every other page are real

    sid = uuid.uuid4().hex[:12]
    bus = EventLog()
    run = pipeline.Run(
        cfg=pipeline.RunConfig(lesson_id="sharing", media=True, run_dir=ROOT / "runs" / sid, fixture="benign/bunny-bow-carrot", ledger_name=a.name, pictures="auto"),
        drawing=media.prepare(src), bus=bus, story_id=sid,
    )  # fmt: skip
    pipeline.execute(run)
    evs = bus.all()
    repairs = [e["data"] for e in evs if e["type"] == "scene.repair" and "picture" in str(e["data"].get("because", ""))]
    pic = [v for v in run.verdicts if v.commitment == "image_no_text"]
    print("OUTCOME:", run.outcome, "| trace", run.trace_id)
    print("PICTURE-WORDS VERDICTS:", [(v.scope, v.attempt, v.status, v.judge_model) for v in pic])
    print("PICTURE REPAINTS:", repairs)
    print("PAINT CALLS:", calls["n"])
    tracing.flush()


if __name__ == "__main__":
    main()
