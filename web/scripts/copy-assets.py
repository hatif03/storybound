"""One-off, repeatable: copy ONLY the assets the web app uses from the read-only D:/neatlogs/assets into web/public/assets.
Run: python scripts/copy-assets.py   (needs Pillow). PNG stills are re-encoded to WebP; everything else is copied as is."""
from __future__ import annotations
import shutil
from pathlib import Path
from PIL import Image

SRC = Path("D:/neatlogs/assets")
DST = Path(__file__).resolve().parent.parent / "public" / "assets"

def cp(rel: str, to: str | None = None) -> None:
    d = DST / (to or rel); d.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(SRC / rel, d)

def webp(rel: str, to: str, max_side: int = 640, q: int = 82) -> None:
    im = Image.open(SRC / rel).convert("RGBA"); im.thumbnail((max_side, max_side))
    d = DST / to; d.parent.mkdir(parents=True, exist_ok=True); im.save(d, "WEBP", quality=q, method=6)

# fonts (SIL OFL) with licences
for f in ["Andika-Regular.woff2", "Andika-Bold.woff2", "Fredoka-Variable.woff2", "AtkinsonHyperlegible-Regular.woff2",
          "AtkinsonHyperlegible-Bold.woff2", "LICENSE-Andika.txt", "LICENSE-Fredoka.txt", "LICENSE-AtkinsonHyperlegible.txt"]:
    cp(f"fonts/{f}", f"fonts/{f}")

# Pip: Rive poses (not 03 crying / 08 angry: never shown to a child), stills as WebP fallback, composites
owls = {"01": "happy-flap", "02": "wink", "04": "cool-sunglasses", "05": "heart-eyes", "06": "dizzy-confused",
        "07": "shocked", "09": "hungry-daydream", "10": "party-cupcake", "11": "shy-giggle", "12": "heart-balloon",
        "13": "bubble-wand", "14": "balloons-party", "15": "birthday-cake"}
for n, name in owls.items():
    cp(f"animation/owls/pip-{n}-{name}.riv", f"pip/pip-{n}-{name}.riv")
    webp(f"animation/owl-stills/owl-{n}-{name}.png", f"pip/pip-{n}-{name}.webp", 480)
for c in ["check", "comfort", "paint", "read"]:
    webp(f"animation/owl-composites/pip-{c}.png", f"pip/pip-{c}.webp", 480)

# brand
cp("brand/logo/storybound-wordmark-color.svg", "brand/wordmark.svg")
webp("brand/logo/storybound-mark-512.png", "brand/mark.webp", 384)
for f in ["favicon.svg", "favicon.ico", "apple-touch-icon.png", "favicon-32.png", "android-chrome-192.png", "android-chrome-512.png"]:
    cp(f"brand/favicon/{f}", f"brand/{f}")
cp("brand/social/og-1200x630.png", "brand/og.png")

# lesson cards (all 12: the backend may add lessons) and scenes (placeholder art for demo mode)
for p in (SRC / "art/lesson-cards").glob("*.webp"):
    cp(f"art/lesson-cards/{p.name}", f"lessons/{p.name}")
for p in (SRC / "art/scenes").glob("*-4x3.webp"):
    cp(f"art/scenes/{p.name}", f"scenes/{p.name}")

# stickers, ui, crayons, textures
for p in (SRC / "art/stickers/promise").glob("*.svg"):
    cp(f"art/stickers/promise/{p.name}", f"stickers/{p.name}")
for n in ["you-did-it", "amazing", "great-job", "awesome"]:
    cp(f"art/stickers/praise-{n}.webp", f"stickers/praise-{n}.webp")
cp("art/ui/eraser.webp", "ui/eraser.webp")
webp("art/textures/white-paper.webp", "ui/paper.webp", 900, 68)
# Crayons: all 20 files in art/crayons are the SAME pink crayon (identical bytes), so one is recoloured here into the ten
# drawing colours (the same hex values are used for the strokes in src/components/palette.ts).
CRAYONS = {"black": "#2B2B2B", "brown": "#8A5A2B", "red": "#E53935", "orange": "#F58A07", "yellow": "#FFD21F",
           "green": "#4CC35A", "sky": "#29A8E8", "blue": "#2F55D4", "purple": "#8E4FD8", "pink": "#FF6FA5"}

def crayon(hexcol: str) -> Image.Image:
    im = Image.open(SRC / "art/crayons/blue.png").convert("RGBA"); im.thumbnail((200, 520))
    tr, tg, tb = (int(hexcol[i:i + 2], 16) for i in (1, 3, 5)); px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a == 0 or max(r, g, b) - min(r, g, b) < 40:  # transparent or the neutral black bands and label
                continue
            t = max(0.0, min(1.0, (g - 61) / (255 - 61)))  # 0 = body, up to ~0.3 = the lighter band
            px[x, y] = (round(tr + t * (255 - tr)), round(tg + t * (255 - tg)), round(tb + t * (255 - tb)), a)
    return im

for name, col in CRAYONS.items():
    d = DST / f"crayons/{name}.webp"; d.parent.mkdir(parents=True, exist_ok=True); crayon(col).save(d, "WEBP", quality=88, method=6)

# icons (Phosphor, MIT)
icons = ["arrow-left", "arrow-right", "arrow-counter-clockwise", "arrows-clockwise", "trash", "check", "check-circle",
         "camera", "speaker-high", "speaker-slash", "star", "door", "lock", "gear", "play", "music-notes", "copy",
         "printer", "x", "house", "receipt", "heart", "seal-check", "shield-check", "warning", "clock", "magnifying-glass",
         "paint-brush", "book-open-text", "sparkle", "smiley", "upload-simple", "lightbulb", "gift", "flask", "text-aa",
         "wrench", "hand-pointing", "image", "eye", "info", "list", "plus", "palette", "stamp", "caret-down", "cloud"]
for i in icons:
    for w in ("fill", "bold"):
        if (SRC / f"icons/{w}/{i}.svg").exists():
            cp(f"icons/{w}/{i}.svg", f"icons/{w}/{i}.svg")

# sound: effects, one quiet music loop (off by default), Pip voice lines, lesson and sticker voices
for f in ["tap", "select", "page-turn", "happy-chime", "soft-boop", "star-pop", "refusal", "silent-100ms"]:
    cp(f"audio/sfx/{f}.mp3", f"audio/sfx/{f}.mp3")
cp("audio/music/happy-lullaby.mp3", "audio/music/happy-lullaby.mp3")
for f in (SRC / "audio/voice/pip").glob("*.mp3"):
    cp(f"audio/voice/pip/{f.name}", f"audio/voice/{f.name}")
for f in ["sharing", "honesty", "kindness", "patience"]:
    cp(f"audio/voice/lessons/{f}.mp3", f"audio/voice/lesson-{f}.mp3")
for f in (SRC / "audio/voice/stickers").glob("*.mp3"):
    cp(f"audio/voice/stickers/{f.name}", f"audio/voice/{f.name}")
print("done")

# demo-mode sample drawings (benign test drawings, CC0/public domain; see test-drawings/SOURCES.md), as small WebP
for p in ["bunny-bow-carrot.png", "rabbit-tree-rainbow.jpg", "rhinoceros-crayon.jpg", "van-crayon.jpg",
          "chameleon-hummingbird.jpg", "christmas-tree-digital.jpg"]:
    webp(f"test-drawings/benign/{p}", f"samples/{Path(p).stem}.webp", 640, 80)
