"""Aggregate a sweep from evidence/ledger.jsonl into a markdown report (and JSON for EVIDENCE.md).

python scripts/report.py --name sweep-1 [--out evidence/reports]
"""

from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from storybound import ledger  # noqa: E402


def rate(n: int, d: int) -> str:
    return f"{n}/{d}" + (f" ({100 * n / d:.0f}%)" if d else "")


def summarise(rows: list[dict]) -> dict:
    by_arm: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_arm[r["arm"]].append(r)
    out: dict = {"arms": {}}
    for arm, rs in sorted(by_arm.items()):
        stories = [r for r in rs if r["outcome"] in ("shipped", "shipped_with_notes", "stopped")]
        shipped = [r for r in stories if r["outcome"] in ("shipped", "shipped_with_notes")]
        with_viol = [r for r in shipped if r["shipped"]]
        first_pass = [r for r in stories if r.get("first_pass_failed")]
        ship_counts = Counter(s["commitment"] for r in shipped for s in r["shipped"])
        fp_counts = Counter(c for r in stories for c in r.get("first_pass_failed", []))
        tier_b = [r for r in stories if r["fixture"].startswith("tier-b-text")]
        obeyed = [r for r in tier_b if any(s["commitment"] == "no_drawing_text_obedience" for s in r["shipped"])]
        obey_seen = [r for r in tier_b if "no_drawing_text_obedience" in r.get("first_pass_failed", [])]
        secs = [r["budget"]["seconds"] for r in stories if r.get("budget")]
        usd = [r["budget"]["usd_estimate"] for r in stories if r.get("budget")]
        first = [r["budget"]["first_page_s"] for r in stories if (r.get("budget") or {}).get("first_page_s")]
        tok = [r["budget"]["tokens_in"] + r["budget"]["tokens_out"] for r in stories if r.get("budget")]
        reps = [r["counts"]["repairs"] for r in stories if r.get("counts")]
        out["arms"][arm] = {
            "runs": len(rs),
            "errors": sum(1 for r in rs if r.get("error")),
            "refused_or_redraw": sum(1 for r in rs if r["outcome"] in ("refused", "ask_redraw")),
            "stories": len(stories),
            "stopped_critical": sum(1 for r in stories if r["outcome"] == "stopped"),
            "shipped_with_violation": len(with_viol),
            "shipped": len(shipped),
            "shipped_violations_total": sum(len(r["shipped"]) for r in shipped),
            "first_pass_any_failure": len(first_pass),
            "first_pass_by_commitment": dict(fp_counts.most_common()),
            "shipped_by_commitment": dict(ship_counts.most_common()),
            "drawing_text_obeyed_in_shipped": len(obeyed),
            "drawing_text_leak_seen_first_pass": len(obey_seen),
            "tier_b_stories": len(tier_b),
            "repairs_mean": round(st.mean(reps), 2) if reps else 0,
            "seconds_mean": round(st.mean(secs), 1) if secs else 0,
            "first_page_s_mean": round(st.mean(first), 1) if first else None,
            "usd_est_mean": round(st.mean(usd), 4) if usd else 0,
            "tokens_mean": round(st.mean(tok)) if tok else 0,
            "judge_errors": sum(r.get("judge_errors", 0) for r in stories),
            "judged": sum(r.get("judged", 0) for r in stories),
        }
    return out


def markdown(name: str, rows: list[dict], s: dict) -> str:
    arms = s["arms"]
    L = [
        f"# Sweep `{name}`",
        "",
        f"{len(rows)} runs. Same drawings, lessons and seeds in both arms; pictures and narration off.",
        "",
    ]
    L += ["| Metric | " + " | ".join(arms) + " |", "| --- | " + " | ".join("---" for _ in arms) + " |"]

    def row(label, fn):
        L.append(f"| {label} | " + " | ".join(fn(a) for a in arms.values()) + " |")

    row("Runs (errors)", lambda a: f"{a['runs']} ({a['errors']})")
    row("Refused or asked to redraw", lambda a: str(a["refused_or_redraw"]))
    row("Stories made", lambda a: str(a["stories"]))
    row("**Shipped with a broken promise**", lambda a: "**" + rate(a["shipped_with_violation"], a["shipped"]) + "**")
    row("Broken promises shipped (total)", lambda a: str(a["shipped_violations_total"]))
    row("Stopped on a critical safety failure", lambda a: str(a["stopped_critical"]))
    row("A promise broken on the first pass", lambda a: rate(a["first_pass_any_failure"], a["stories"]))
    row(
        "Drawing text reached the shipped story",
        lambda a: rate(a["drawing_text_obeyed_in_shipped"], a["tier_b_stories"]),
    )
    row(
        "Drawing text leaked on first pass", lambda a: rate(a["drawing_text_leak_seen_first_pass"], a["tier_b_stories"])
    )
    row("Repairs per story (mean)", lambda a: str(a["repairs_mean"]))
    row("Seconds per story (mean)", lambda a: str(a["seconds_mean"]))
    row("Seconds to first page (mean)", lambda a: "n/a" if a["first_page_s_mean"] is None else str(a["first_page_s_mean"]))
    row("Estimated USD per story (mean)", lambda a: f"{a['usd_est_mean']:.4f}")
    row("Tokens per story (mean)", lambda a: f"{a['tokens_mean']:,}")
    row("Judge calls that could not verify", lambda a: rate(a["judge_errors"], a["judged"]))
    L += ["", "## Broken on the first pass, by promise", ""]
    names = sorted({c for a in arms.values() for c in a["first_pass_by_commitment"]})
    L += ["| Promise | " + " | ".join(arms) + " |", "| --- | " + " | ".join("---" for _ in arms) + " |"]
    for c in names:
        L.append(f"| `{c}` | " + " | ".join(str(a["first_pass_by_commitment"].get(c, 0)) for a in arms.values()) + " |")
    L += ["", "## Shipped broken, by promise", ""]
    names = sorted({c for a in arms.values() for c in a["shipped_by_commitment"]})
    if names:
        L += ["| Promise | " + " | ".join(arms) + " |", "| --- | " + " | ".join("---" for _ in arms) + " |"]
        for c in names:
            L.append(
                f"| `{c}` | " + " | ".join(str(a["shipped_by_commitment"].get(c, 0)) for a in arms.values()) + " |"
            )
    else:
        L.append("Nothing shipped broken in any arm.")
    L += ["", "Cost figures are estimates from token counts; neatlogs holds the measured numbers.", ""]
    return "\n".join(L)


def rows_for(name: str) -> list[dict]:
    """Ledger rows of one named sweep; a re-run of the same job replaces an earlier errored attempt."""
    latest: dict[tuple, dict] = {}
    for r in ledger.read():
        if r.get("name") == name and r.get("arm"):
            latest[(r["arm"], r["fixture"], r["lesson"], str(r["seed"]))] = r
    return list(latest.values())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--out", default=str(ROOT / "evidence" / "reports"))
    a = ap.parse_args()
    rows = rows_for(a.name)
    if not rows:
        sys.exit(f"no ledger rows named {a.name}")
    s = summarise(rows)
    md = markdown(a.name, rows, s)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{ledger.stamp(a.name)}.md").write_text(md, encoding="utf-8")
    (out / f"{ledger.stamp(a.name)}.json").write_text(json.dumps(s, indent=2), encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
