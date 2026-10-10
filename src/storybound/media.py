"""Drawing intake: validate, flatten transparency onto white, fix orientation, downscale. No model calls."""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass

from PIL import Image, ImageOps

MAX_UPLOAD = 8 * 1024 * 1024
MAX_SIDE = 1568
MIN_SIDE = 96


class BadDrawing(ValueError):
    """The upload is not a usable image. `code` is safe to show a child's grown-up."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass
class Drawing:
    data: bytes  # normalised JPEG sent to models
    mime: str
    width: int
    height: int
    sha256: str  # of the original upload, so a rerun is recognisable without storing the picture
    too_small: bool = False
    blank: bool = False


def prepare(raw: bytes) -> Drawing:
    if not raw:
        raise BadDrawing("bad_input", "No picture was sent.")
    if len(raw) > MAX_UPLOAD:
        raise BadDrawing("too_large", "That picture is too big. Please try one under 8 MB.")
    try:
        im = Image.open(io.BytesIO(raw))
        im.load()
    except Exception as e:
        raise BadDrawing("bad_input", "That file does not look like a picture.") from e
    im = ImageOps.exif_transpose(im)
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        bg = Image.new("RGB", im.size, (255, 255, 255))
        im = im.convert("RGBA")
        bg.paste(im, mask=im.split()[-1])
        im = bg
    else:
        im = im.convert("RGB")
    w, h = im.size
    too_small = min(w, h) < MIN_SIDE
    if max(w, h) > MAX_SIDE:
        im.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
    gray = im.convert("L").resize((64, 64))
    lo, hi = gray.getextrema()
    blank = (hi - lo) < 12  # almost no ink at all
    out = io.BytesIO()
    im.save(out, "JPEG", quality=90)
    return Drawing(out.getvalue(), "image/jpeg", w, h, hashlib.sha256(raw).hexdigest(), too_small, blank)


def web_image(data: bytes, max_side: int = 1024, quality: int = 82) -> bytes:
    """Illustrations are 2 MB PNGs; the web needs a small JPEG (target well under 250 KB)."""
    im = Image.open(io.BytesIO(data)).convert("RGB")
    im.thumbnail((max_side, max_side), Image.LANCZOS)
    out = io.BytesIO()
    im.save(out, "JPEG", quality=quality, optimize=True)
    return out.getvalue()
