"""Put the sound and the voice-over back into the recorded walkthrough of the app.

  python scripts/compose_demo.py [--speed 12] [--offset 0.0]

Reads evidence/app-capture/work/ (frames, cues.json, audio/*) made by web/scripts/record-demo.mjs and evidence/app-capture/voiceover/.
Writes evidence/app-capture/:
  app-walkthrough.mp4        the whole recording at normal speed, with every sound the app made and the voice-over
  app-walkthrough-cut.mp4    the same with the waiting stretches sped up (and silent), ready to use
  app-walkthrough-cues.txt   when each thing happens in the full-length file (for cutting it by hand)
The browser that records has no sound card, so the sound is rebuilt: each sound the app played was logged with its time and is placed at that time.
While a voice-over line plays, the app's own sounds are turned down to 30%.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "evidence" / "app-capture"
WORK = DEMO / "work"
FFMPEG = "C:/ffmpeg/ffmpeg.exe"
FFPROBE = "C:/ffmpeg/ffprobe.exe"


def duration(path: Path) -> float:
    out = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def app_sounds(data: dict, offset: float) -> list[dict]:
    """Each sound the app played: file, start and end in seconds on the video's clock, volume."""
    t0 = data["recStart"]
    files = data["files"]
    by_id: dict[int, list[dict]] = {}
    for e in sorted(data["audio"], key=lambda e: e["t"]):
        by_id.setdefault(e["id"], []).append(e)
    total = (data["end"] - t0) / 1000 + offset
    out = []
    for evs in by_id.values():
        cur = None

        def close(end_s: float) -> None:
            nonlocal cur
            if cur is not None:
                cur["end"] = min(cur["end"], end_s)
                out.append(cur)
                cur = None

        for e in evs:
            s = (e["t"] - t0) / 1000 + offset
            if e["e"] == "play":
                close(s)
                f = files.get(e["src"])
                if not f or "silent-100ms" in f:
                    continue
                path = WORK / "audio" / f
                length = total - s if e.get("loop") else duration(path)
                cur = {"file": path, "start": s, "end": s + length, "vol": float(e["vol"]), "music": bool(e.get("loop"))}
            elif e["e"] in ("pause", "ended") and cur is not None and (e["t"] - t0) / 1000 + offset > cur["start"] + 0.08:
                close(s)
        close(total)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--speed", type=float, default=12.0, help="speed of the waiting stretches in the cut")
    ap.add_argument("--offset", type=float, default=0.0, help="seconds to shift every sound later (the video starts a little after the cues clock)")
    a = ap.parse_args()
    data = json.loads((WORK / "cues.json").read_text(encoding="utf-8"))
    vo_dir = DEMO / "voiceover"
    frames = json.loads((WORK / "frames.json").read_text(encoding="utf-8"))  # [epoch ms, file]: each frame is shown from its time until the next frame's
    t0 = frames[0][0]  # the video starts at the first frame; every sound is placed relative to it
    data["recStart"] = t0
    end_ms = max(data["end"], frames[-1][0] + 1000)
    video_in = WORK / "screen.mp4"
    if not video_in.exists():
        lst = WORK / "frames.txt"
        rows = []
        for i, (t, name) in enumerate(frames):
            nxt = frames[i + 1][0] if i + 1 < len(frames) else end_ms
            rows.append(f"file 'frames/{name}'")
            rows.append(f"duration {max(0.001, (nxt - t) / 1000):.3f}")
        rows.append(f"file 'frames/{frames[-1][1]}'")  # the concat demuxer ignores the duration of the last entry unless it is repeated
        lst.write_text(chr(10).join(rows), encoding="utf-8")
        subprocess.run([FFMPEG, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-crf", "20", "-preset", "veryfast", str(video_in)], check=True)
    vlen = duration(video_in)
    total = max(vlen, (end_ms - t0) / 1000)
    print(f"video {vlen:.1f}s, cues clock {(end_ms - t0) / 1000:.1f}s")

    sounds = app_sounds(data, a.offset)
    vo = [{"file": vo_dir / f"{c['key']}.mp3", "start": (c["t"] - t0) / 1000 + a.offset, "end": (c["t"] - t0) / 1000 + a.offset + c["seconds"]} for c in data["cues"] if c["type"] == "vo"]
    print(f"{len(sounds)} app sounds, {len(vo)} voice-over lines")

    inputs: list[str] = []
    graph: list[str] = []

    def add(item: dict, label: str, vol: float) -> None:
        idx = len(inputs) // 2
        inputs.extend(["-i", str(item["file"])])
        ms = max(0, int(item["start"] * 1000))
        length = max(0.05, item["end"] - item["start"])
        fade = f",afade=t=out:st={max(0.0, length - 0.15):.2f}:d=0.15" if length < duration(item["file"]) - 0.2 else ""
        graph.append(f"[{idx}:a]aformat=sample_rates=44100:channel_layouts=stereo,atrim=0:{length:.3f},volume={vol:.3f}{fade},adelay={ms}|{ms}[{label}]")

    app_labels, vo_labels = [], []
    for i, s in enumerate(sounds):
        add(s, f"a{i}", 0.07 if s["music"] else min(1.0, s["vol"]) * (1.0 if s["vol"] >= 0.9 else 1.3))
        app_labels.append(f"[a{i}]")
    for i, v in enumerate(vo):
        add(v, f"v{i}", 1.25)
        vo_labels.append(f"[v{i}]")
    duck = "+".join(f"between(t,{v['start'] - 0.1:.2f},{v['end'] + 0.3:.2f})" for v in vo) or "0"
    graph.append(f"{''.join(app_labels)}amix=inputs={len(app_labels)}:normalize=0:duration=longest,volume=0.3:enable='gt({duck},0)'[app]")
    graph.append(f"{''.join(vo_labels)}amix=inputs={len(vo_labels)}:normalize=0:duration=longest[vo]")
    graph.append(f"[app][vo]amix=inputs=2:normalize=0:duration=longest,volume=2.0,alimiter=limit=0.95,apad,atrim=0:{total:.2f}[mix]")
    gfile = WORK / "mix-graph.txt"
    gfile.write_text(";\n".join(graph), encoding="utf-8")
    mix = WORK / "mix.wav"
    subprocess.run([FFMPEG, "-y", "-v", "error", *inputs, "-filter_complex_script", str(gfile), "-map", "[mix]", "-ar", "44100", str(mix)], check=True)
    print("mixed the sound")

    full = DEMO / "app-walkthrough.mp4"
    subprocess.run([FFMPEG, "-y", "-v", "error", "-i", str(video_in), "-i", str(mix), "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", str(full)], check=True)
    print("wrote", full)

    # the cut: waiting stretches are sped up and silent
    waits = sorted(((c["from"] - t0) / 1000 + a.offset, (c["to"] - t0) / 1000 + a.offset) for c in data["cues"] if c["type"] == "wait")
    waits = [(f, t) for f, t in waits if t - f > 3 and t <= vlen + 1]
    segs, pos = [], 0.0
    for f, t in waits:
        if f > pos:
            segs.append((pos, f, 1.0))
        segs.append((f, t, a.speed))
        pos = t
    segs.append((pos, vlen, 1.0))
    parts, labels = [], []
    for k, (f, t, sp) in enumerate(segs):
        parts.append(f"[0:v]trim={f:.3f}:{t:.3f},setpts=(PTS-STARTPTS)/{sp}[v{k}]")
        if sp == 1.0:
            parts.append(f"[1:a]atrim={f:.3f}:{t:.3f},asetpts=PTS-STARTPTS[a{k}]")
        else:
            parts.append(f"anullsrc=r=44100:cl=stereo,atrim=0:{(t - f) / sp:.3f}[a{k}]")
        labels.append(f"[v{k}][a{k}]")
    parts.append(f"{''.join(labels)}concat=n={len(segs)}:v=1:a=1[v][a]")
    cfile = WORK / "cut-graph.txt"
    cfile.write_text(";\n".join(parts), encoding="utf-8")
    cut = DEMO / "app-walkthrough-cut.mp4"
    subprocess.run([FFMPEG, "-y", "-v", "error", "-i", str(video_in), "-i", str(mix), "-filter_complex_script", str(cfile), "-map", "[v]", "-map", "[a]", "-r", "30", "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "20", "-preset", "medium", "-c:a", "aac", "-b:a", "160k", str(cut)], check=True)
    print("wrote", cut, f"({duration(cut):.0f}s; waiting sped up {a.speed:g}x over {sum(t - f for f, t in waits):.0f}s)")

    lines = ["Full-length file (app-walkthrough.mp4): time, what", ""]
    for c in sorted(data["cues"], key=lambda c: c.get("t") or c.get("from")):
        s = ((c.get("t") or c["from"]) - t0) / 1000 + a.offset
        what = {"vo": lambda c: f"voice-over: {c['key']} ({c['seconds']}s)", "page": lambda c: f"page {c['page']} shown (picture: {c['picture']})", "wait": lambda c: f"WAITING {(c['to'] - c['from']) / 1000:.0f}s (sped up in the cut)"}[c["type"]](c)
        lines.append(f"{int(s // 60)}:{s % 60:04.1f}  {what}")
    (DEMO / "app-walkthrough-cues.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
