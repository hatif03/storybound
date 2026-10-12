"""Build the demo videos from the recordings and the voice-over: the 3-minute pitch video and the full tour.

  python scripts/build_pitch_video.py pitch        # evidence/demo/storybound-demo-3min.mp4 (at most 3:00)
  python scripts/build_pitch_video.py tour         # evidence/full-tour/storybound-full-tour.mp4 (every feature, including the grown-up side)

Sources (screen recordings, silent unless noted): evidence/app-capture/app-walkthrough.mp4 (the app, with its own sound; its sound without the voice-over is
work/apponly.wav), the three dashboard recordings neatlogs.mp4, entire.mp4, cfo.ai.mp4 at the repo root, and evidence/features-capture/. The voice-over is
text-to-speech (scripts/make_demo_voiceover.py). Each scene is one voice-over line over one or more clips, with an optional caption; a scene lasts as long as
its voice-over (or its clips, if longer). Links on the end card come from evidence/demo/links.json (live, demo, code).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FFMPEG = "C:/ffmpeg/ffmpeg.exe"
FFPROBE = "C:/ffmpeg/ffprobe.exe"
FONT = "C\\:/Windows/Fonts/arialbd.ttf"
W, H = 1920, 1080
VO_TEMPO = 1.12  # the text-to-speech voice is unhurried; a little faster fits three minutes and still sounds natural

AC = ROOT / "evidence" / "app-capture"
FC = ROOT / "evidence" / "features-capture"
SRC = {"aw": AC / "app-walkthrough.mp4", "nl": ROOT / "neatlogs.mp4", "en": ROOT / "entire.mp4", "cf": ROOT / "cfo.ai.mp4"}


def dur(p: Path) -> float:
    o = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)], capture_output=True, text=True, check=True)
    return float(o.stdout.strip())


def part(src: str, start: float, d: float, speed: float = 1.0, audio: float = 0.0, file: Path | None = None, audio_file: Path | None = None) -> dict:
    return {"file": file or SRC[src], "start": start, "d": d, "speed": speed, "audio": audio, "audio_file": audio_file or (AC / "work" / "apponly.wav")}


def cap(text: str, a: float, b: float) -> tuple[str, float, float]:
    return (text, a, b)


def esc(text: str) -> str:
    return text.replace("\\", "\\\\").replace("'", "\u2019").replace(":", "\\:").replace("%", "\\%").replace(",", "\\,")


def build_scene(k: int, out: Path, vo: Path | None, parts: list[dict], captions: list, card: list[str] | None = None, min_d: float = 0.0, lead: float = 0.3) -> float:
    vo_d = dur(vo) / VO_TEMPO if vo else 0.0
    clip_d = sum(p["d"] / p["speed"] for p in parts) if parts else 0.0
    D = max(clip_d, vo_d + lead + 0.5, min_d)
    ins: list[str] = []
    f: list[str] = []
    n = 0
    labels = []
    for i, p in enumerate(parts):
        ins += ["-ss", f"{p['start']:.3f}", "-t", f"{p['d']:.3f}", "-i", str(p["file"])]
        f.append(f"[{n}:v]setpts=(PTS-STARTPTS)/{p['speed']},scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p,setsar=1[p{i}]")
        labels.append(f"[p{i}]")
        n += 1
    if parts:
        f.append(f"{''.join(labels)}concat=n={len(parts)}:v=1:a=0[vc]")
        pad = f",tpad=stop_mode=clone:stop_duration={max(0.0, D - clip_d):.3f}" if D > clip_d + 0.01 else ""
        f.append(f"[vc]null{pad}[vb]")
    else:
        f.append(f"color=c=0x1b1a2e:s={W}x{H}:d={D:.3f}:r=30,format=yuv420p[vb]")
    cur = "vb"
    j = 0
    if card:
        y = 250
        for line, size in [(l.split("|")[0], int(l.split("|")[1]) if "|" in l else 54) for l in card]:
            f.append(f"[{cur}]drawtext=fontfile='{FONT}':text='{esc(line)}':fontsize={size}:fontcolor=white:x=(w-text_w)/2:y={y}[c{j}]")
            cur = f"c{j}"
            j += 1
            y += int(size * 1.9)
    for text, a, b in captions:
        f.append(f"[{cur}]drawtext=fontfile='{FONT}':text='{esc(text)}':fontsize=46:fontcolor=white:box=1:boxcolor=black@0.62:boxborderw=22:x=(w-text_w)/2:y=h-150:enable='between(t,{a:.2f},{b:.2f})'[c{j}]")
        cur = f"c{j}"
        j += 1
    f.append(f"[{cur}]null[v]")
    # audio: the voice-over (a little after the scene starts) and any real narration under it
    alabels = []
    if vo:
        ins += ["-i", str(vo)]
        f.append(f"[{n}:a]aformat=sample_rates=44100:channel_layouts=stereo,atempo={VO_TEMPO},volume=1.3,adelay={int(lead * 1000)}|{int(lead * 1000)}[va]")
        alabels.append("[va]")
        n += 1
    off = 0.0
    for p in parts:
        if p["audio"] > 0:
            ins += ["-ss", f"{p['start']:.3f}", "-t", f"{p['d']:.3f}", "-i", str(p["audio_file"])]
            f.append(f"[{n}:a]aformat=sample_rates=44100:channel_layouts=stereo,volume={p['audio']},adelay={int(off * 1000)}|{int(off * 1000)}[ra{n}]")
            alabels.append(f"[ra{n}]")
            n += 1
        off += p["d"] / p["speed"]
    if alabels:
        f.append(f"{''.join(alabels)}amix=inputs={len(alabels)}:normalize=0:duration=longest,apad,atrim=0:{D:.3f}[a]")
    else:
        f.append(f"anullsrc=r=44100:cl=stereo,atrim=0:{D:.3f}[a]")
    gf = out.with_suffix(".graph.txt")
    gf.write_text(";\n".join(f), encoding="utf-8")
    subprocess.run([FFMPEG, "-y", "-v", "error", *ins, "-filter_complex_script", str(gf), "-map", "[v]", "-map", "[a]", "-t", f"{D:.3f}", "-r", "30", "-c:v", "libx264", "-crf", "20", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", str(out)], check=True)
    return D


def concat(scenes: list[Path], out: Path) -> None:
    lst = out.with_suffix(".txt")
    lst.write_text("\n".join(f"file '{s.as_posix()}'" for s in scenes), encoding="utf-8")
    subprocess.run([FFMPEG, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out)], check=True)


def cues(path: Path) -> dict:
    d = json.loads(path.read_text(encoding="utf-8"))
    t0 = json.loads((path.parent / "frames.json").read_text(encoding="utf-8"))[0][0] if (path.parent / "frames.json").exists() else d["recStart"]
    vo = {c["key"]: (c["t"] - t0) / 1000 for c in d["cues"] if c["type"] == "vo"}
    page = {c["page"]: (c["t"] - t0) / 1000 for c in d["cues"] if c["type"] == "page"}
    waits = [((c["from"] - t0) / 1000, (c["to"] - t0) / 1000) for c in d["cues"] if c["type"] == "wait"]
    return {"vo": vo, "page": page, "waits": waits, "t0": t0}


def links() -> dict:
    p = ROOT / "evidence" / "demo" / "links.json"
    base = {"live": "<live app link>", "demo": "<demo link>", "code": "github.com/hatif03/storybound"}
    if p.exists():
        base.update(json.loads(p.read_text(encoding="utf-8")))
    return base


def pitch() -> None:
    work = ROOT / "evidence" / "pitch-video" / "work"
    work.mkdir(parents=True, exist_ok=True)
    vdir = ROOT / "evidence" / "pitch-video" / "voiceover"
    c = cues(AC / "work" / "cues.json") if (AC / "work" / "cues.json").exists() else cues(AC / "recording-cues.json")
    long_from, long_to = max(c["waits"], key=lambda w: w[1] - w[0])  # the longest wait: the agent writing and checking page after page
    lk = links()
    scenes = [
        ("c1", [part("aw", c["vo"]["draw"] + 1, 17, 1.0)], [cap("27 of 28 AI-written stories broke a promise", 5.5, 16)], None),
        ("c2", [part("aw", c["vo"]["lesson"] - 3, 20, 1.0)], [cap("Promises first: a checkable oath for each drawing and lesson", 3, 20)], None),
        ("c3", [part("aw", long_from + 45, 16, 1.0)], [cap("Every page is checked before the child sees it", 2, 16)], None),
        ("c4", [part("aw", c["page"][1] - 0.3, 14, 1.0, audio=0.45)], [cap("It reads itself aloud, with a replay button", 1.5, 8), cap("Kind choices and a verified quiz", 8, 14)], None),
        ("c5", [part("aw", c["vo"]["receipt"] - 0.5, 15, 1.0)], [cap("The receipt: nothing hidden. 0 of 28 shipped a broken promise", 2, 15)], None),
        ("c6", [part("nl", 22, 12, 1.0)], [cap("neatlogs: one trace per story, every promise a quoted verdict", 1, 11)], None),
        ("c7", [part("nl", 66, 24, 1.0), part("nl", 94, 6, 1.0)], [cap("Writer broke the page format: 3 of 10 failed, then 10 of 10", 1, 10), cap("Judge down: 0 of 5 shipped, with a second judge 5 of 5", 10, 18.5), cap("Repair loop never ends? No: our tracing lost spans. Fixed.", 18.5, 30)], None),
        ("c9", [part("en", 8, 5, 1.0), part("en", 16, 4, 1.0), part("en", 30, 4, 1.0)], [cap("Entire: one checkpoint per fix, a review, runners that gate the next change", 1, 13)], None),
        ("c10", [part("cf", 5, 11, 1.0), part("cf", 26, 7, 1.0)], [cap("cfo.ai: the cost of a story became a product decision", 1, 18)], None),
        ("c11", [], [], ["Storybound|96", "Promises first. Checked before the child sees a page.|46", "A receipt for the parent.|46", f"Live app: {lk['live']}|40", f"Free demo: {lk['demo']}|40", f"Code: {lk['code']}|40", "#neatHack  @neatlogs  @EntireHQ  @arithecfo|36"]),
    ]
    out_scenes, total = [], 0.0
    for k, (vid, parts, caps, card) in enumerate(scenes):
        out = work / f"scene{k:02d}.mp4"
        d = build_scene(k, out, vdir / f"{vid}.mp3", parts, caps, card, min_d=(10.0 if vid == "c11" else 0.0))
        total += d
        out_scenes.append(out)
        print(f"{vid}: {d:.1f}s (total {total:.1f}s)", flush=True)
    final = ROOT / "evidence" / "demo" / "storybound-demo-3min.mp4"
    final.parent.mkdir(parents=True, exist_ok=True)
    concat(out_scenes, final)
    print("wrote", final, f"{dur(final):.1f}s")
    if dur(final) > 180:
        sys.exit(f"too long: {dur(final):.1f}s")


def tour() -> None:
    sys.exit("tour: built by scripts/build_pitch_video.py after the feature recording; see build_tour() once the recording exists")


if __name__ == "__main__":
    {"pitch": pitch, "tour": tour}[sys.argv[1] if len(sys.argv) > 1 else "pitch"]()
