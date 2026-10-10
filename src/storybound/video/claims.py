"""Claims resolve against evidence files at render time. This is the only place a number can enter a video."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from .spec import Claim, Spec

ROOT = Path(__file__).resolve().parents[3]
EV = ROOT / "evidence"


def _file(ref: str) -> Path:
    kind, _, rest = ref.partition(":")
    name = rest.split("#", 1)[0]
    if kind == "report":
        files = sorted((EV / "reports").glob(f"*-{name}.json"))  # the latest report of that sweep
        if not files:
            raise FileNotFoundError(f"no report for sweep '{name}'")
        return files[-1]
    if kind == "file":
        p = (ROOT / name).resolve()
        if ROOT not in p.parents or "_private" in p.parts:
            raise ValueError(f"claim file outside the repo or private: {name}")
        return p
    raise ValueError(f"unknown claim source '{ref}'")


def _dig(obj: Any, path: str) -> Any:
    for part in path.split("."):
        obj = obj[int(part)] if isinstance(obj, list) else obj[part]
    return obj


def _num(x: Any) -> Any:
    return x if isinstance(x, (int, float)) else float(x)


def resolve_claim(c: Claim) -> dict:
    sources, values = [], []
    for ref in c.refs:
        f = _file(ref)
        v = _num(_dig(json.loads(f.read_text(encoding="utf-8")), ref.split("#", 1)[1]))
        values.append(v)
        sources.append({"ref": ref, "file": str(f.relative_to(ROOT)).replace("\\", "/"), "value": v,
                        "sha256": hashlib.sha256(f.read_bytes()).hexdigest()[:16]})  # fmt: skip
    return {
        "id": c.id, "label": c.label, "display": c.fmt.format(*values),
        "spoken": (c.spoken or c.fmt).format(*values),
        "ratio": (values[0] / values[1]) if c.ratio and values[1] else None,
        "sources": sources,
    }  # fmt: skip


def resolve(spec: Spec) -> dict[str, dict]:
    return {c.id: resolve_claim(c) for c in spec.claims}


def _report_module():
    p = ROOT / "scripts" / "report.py"
    s = importlib.util.spec_from_file_location("storybound_report_script", p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)  # type: ignore[union-attr]
    return m


def recompute_from_ledger(ref: str) -> Any:
    """For a `report:` ref, rebuild the number from the raw ledger rows, independent of the saved report file."""
    rep = _report_module()
    name, path = ref.split(":", 1)[1].split("#", 1)
    return _dig(rep.summarise(rep.rows_for(name)), path)
