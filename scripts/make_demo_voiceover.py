"""Make the voice-over clips for the demo video with the project's text-to-speech (a different voice from the story narrator).

  python scripts/make_demo_voiceover.py [--voice Charon]

Reads web/scripts/demo-voiceover.json, writes evidence/app-capture/voiceover/<key>.mp3 and manifest.json (seconds per clip). Needs Google credentials as the app does.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from storybound.clients import tts  # noqa: E402
from storybound.config import get_settings  # noqa: E402

FFPROBE = "C:/ffmpeg/ffprobe.exe"
STYLE = "Speak as a calm, friendly presenter of a product demo, at a steady, unhurried pace."


def seconds(path: Path) -> float:
    out = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True)
    return round(float(out.stdout.strip()), 2)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", default="Charon")
    a = ap.parse_args()
    texts = json.loads((ROOT / "web" / "scripts" / "demo-voiceover.json").read_text(encoding="utf-8"))
    out = ROOT / "evidence" / "app-capture" / "voiceover"
    out.mkdir(parents=True, exist_ok=True)
    model = get_settings().models.tts
    manifest = {}
    for key, text in texts.items():
        data, _lat = tts._once(text, a.voice, model, STYLE)
        p = out / f"{key}.mp3"
        p.write_bytes(data)
        manifest[key] = {"seconds": seconds(p), "text": text}
        print(key, manifest[key]["seconds"], flush=True)
    (out / "manifest.json").write_text(json.dumps({"voice": a.voice, "clips": manifest}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
