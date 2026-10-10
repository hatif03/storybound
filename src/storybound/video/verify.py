"""The video oath: deterministic promises checked before a video ships. Same verdict shape as the story oath."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from .claims import ROOT, recompute_from_ledger
from .spec import Spec

TOOLS = ("neatlogs", "entire", "cfo.ai")
POINTS = ("architecture", "implementation", "runtime", "reasoning", "result")
KEY_LIKE = re.compile(r"(AKIA[0-9A-Z]{16}|ya29\.[0-9A-Za-z_-]{20,}|sk-[A-Za-z0-9]{20,}|IFM-[A-Za-z0-9]{12,}|[A-Za-z0-9]{32,})")
LUFS_RANGE = (-19.0, -13.0)


def _v(commitment: str, ok: bool, expected: str, actual: str, scene: str | None = None) -> dict:
    return {"commitment": commitment, "status": "pass" if ok else "violation", "expected": expected,
            "actual": actual, "scene": scene}  # fmt: skip


def _texts(spec: Spec):
    """Every string that reaches the screen or the narration, except resolved claim values."""
    for s in spec.scenes:
        if s.kind == "story":  # words of an already verified story: the story oath covers them, not ours
            continue
        yield s.id, "narration", s.narration
        for b in s.blocks:
            if b.text:
                yield s.id, f"{b.type} text", b.text
            for it in b.items:
                if isinstance(it, str):
                    yield s.id, "list item", it
                else:
                    yield s.id, "bar label", it.get("label", it.get("text", ""))
    for c in spec.claims:
        yield "claims", f"claim label {c.id}", c.label


OVERCLAIM = re.compile(r"cryptograph\w*|guarantee\w*|perfect\w*|flawless\w*|foolproof|bulletproof|unbreakable|completely safe|zero risk|impossible to", re.I)


def no_overclaims(spec: Spec) -> list[dict]:
    """The receipt is a hash plus a list of verdicts: words that promise more than that are refused."""
    bad = [(sid, where, t) for sid, where, t in _texts(spec) if OVERCLAIM.search(t)]
    if not bad:
        return [_v("no_overclaims", True, "no words promising more than we can show", "none found")]
    return [_v("no_overclaims", False, "no overclaiming words (cryptographic, guaranteed, perfect...)",
               f"'{OVERCLAIM.search(t).group(0)}' in {where}", sid) for sid, where, t in bad]  # fmt: skip


def length_ok(spec: Spec, total: float) -> dict:
    return _v("length_ok", total <= spec.max_seconds, f"at most {spec.max_seconds:.0f} s", f"{total:.1f} s")


def claims_sourced(spec: Spec) -> list[dict]:
    """No digit may appear outside a claim: numbers come from evidence files, never from the writer."""
    bad = [(sid, where, t) for sid, where, t in _texts(spec) if re.search(r"\d", re.sub(r"\{[\w.-]+\}", "", t))]
    if not bad:
        return [_v("claims_sourced", True, "no typed numbers", "none found")]
    return [_v("claims_sourced", False, "no typed numbers; use a claim", f"digit in {where}: '{t[:60]}'", sid) for sid, where, t in bad]


def claims_match_ledger(resolved: dict[str, dict]) -> list[dict]:
    """Rebuild every report-backed number from the raw ledger and compare with what the video shows."""
    out = []
    for cid, r in resolved.items():
        for s in r["sources"]:
            if not s["ref"].startswith("report:"):
                continue
            try:
                again = recompute_from_ledger(s["ref"])
                ok = abs(float(again) - float(s["value"])) < 1e-9
                out.append(_v("claims_match_ledger", ok, f"{s['value']} (report file)", f"{again} (ledger rebuild)", cid))
            except Exception as e:  # the ledger changed shape, a missing path: cannot be verified
                out.append({**_v("claims_match_ledger", False, "rebuild from ledger", f"{type(e).__name__}: {e}", cid), "status": "verification_error"})
    return out or [_v("claims_match_ledger", True, "report-backed claims", "none to check")]


def tools_covered(spec: Spec) -> dict:
    if not spec.requires_coverage:
        return _v("tools_covered", True, "not required for this video", "skipped")
    have = {c for s in spec.scenes for c in s.covers}
    missing = [f"{t}:{p}" for t in TOOLS for p in POINTS if f"{t}:{p}" not in have]
    return _v("tools_covered", not missing, "each tool on all five points", "missing: " + ", ".join(missing) if missing else "all 15 covered")


def _env_secrets() -> list[str]:
    f = ROOT / ".env"
    vals = []
    if f.exists():
        for ln in f.read_text(encoding="utf-8").splitlines():
            if "=" in ln and not ln.lstrip().startswith("#"):
                k, v = ln.split("=", 1)
                v = v.strip().strip("'\"")
                if re.search(r"KEY|SECRET|TOKEN|PASSWORD", k, re.I) and len(v) >= 12:
                    vals.append(v)
    return vals


def no_secrets(spec: Spec, resolved: dict[str, dict]) -> dict:
    blob = json.dumps(spec.model_dump()) + json.dumps(resolved)
    for r in resolved.values():
        for src in r["sources"]:
            blob = blob.replace(src["sha256"], "")  # our own source hashes are not keys; nothing else is stripped
    hit = KEY_LIKE.search(blob)
    leaked = any(v in blob for v in _env_secrets())
    return _v("no_secrets", not hit and not leaked, "no key-like strings, no .env values", "found one" if (hit or leaked) else "none found")


def _image_allowed(src: str) -> bool:
    if "_private" in src or ".." in src:
        return False
    if src.startswith("assets/"):
        return True
    if src.startswith("evidence/stories/"):  # a story package is allowed only if it came from a fixture drawing
        pkg = ROOT / "/".join(src.split("/")[:3]) / "story.json"
        try:
            return bool(json.loads(pkg.read_text(encoding="utf-8")).get("fixture"))
        except Exception:
            return False
    return False


def no_child_data(spec: Spec) -> dict:
    bad = [b.src for s in spec.scenes for b in s.blocks if b.type == "image" and not _image_allowed(b.src)]
    return _v("no_child_data", not bad, "images only from assets/ or a fixture-drawing story package", f"outside the allow-list: {bad}" if bad else "all images allowed")


def static(spec: Spec, resolved: dict[str, dict], total: float) -> list[dict]:
    return [length_ok(spec, total), *claims_sourced(spec), *claims_match_ledger(resolved), *no_overclaims(spec), tools_covered(spec),
            no_secrets(spec, resolved), no_child_data(spec)]  # fmt: skip


def loudness(mp4: Path) -> float | None:
    ff = shutil.which("ffmpeg") or "ffmpeg"
    p = subprocess.run([ff, "-nostats", "-i", str(mp4), "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")  # fmt: skip
    m = re.findall(r"I:\s+(-?\d+\.\d+) LUFS", p.stderr)
    return float(m[-1]) if m else None


def audio_ok(mp4: Path, timeline: dict) -> dict:
    lufs = loudness(mp4)
    if lufs is None:
        return {**_v("audio_ok", False, "measurable loudness", "could not measure"), "status": "verification_error"}
    lo, hi = LUFS_RANGE
    return _v("audio_ok", lo <= lufs <= hi, f"{lo} to {hi} LUFS", f"{lufs} LUFS")


def renders_clean(chk: dict) -> dict:
    return _v("renders_clean", chk["passed"], "HyperFrames check passes (lint, runtime, layout, motion, contrast)",
              "passed" if chk["passed"] else "; ".join(chk["problems"])[:400] or "check failed")  # fmt: skip
