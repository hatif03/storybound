"""Make a video with the video agent.

python scripts/make_video.py --spec video/harness/specs/x.json --out evidence/video/x
python scripts/make_video.py --brief "..." --claims video/harness/claims/preview.json --title preview --out evidence/video/preview
"""

import os

os.environ["NEATLOGS_WORKFLOW"] = "make-video"  # before the tracing module initialises neatlogs

import argparse  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from storybound.video import agent, spec  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec")
    ap.add_argument("--brief", default="")
    ap.add_argument("--claims")
    ap.add_argument("--title", default="video")
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", default="", help="ledger name; empty means no ledger row")
    ap.add_argument("--max-repairs", type=int, default=agent.MAX_REPAIRS)
    a = ap.parse_args()
    s = spec.load(a.spec) if a.spec else None
    catalog = json.loads(Path(a.claims).read_text(encoding="utf-8")) if a.claims else None
    r = agent.make(s, brief=a.brief, catalog=catalog, title=a.title, out=Path(a.out), max_repairs=a.max_repairs, name=a.name)
    last = r["attempts"][-1]["verdicts"] if r.get("attempts") else []
    print(json.dumps({"outcome": r.get("outcome"), "trace_id": r.get("trace_id"), "repairs": r["repairs"],
                      "broken": r.get("broken"), "video": r.get("video"), "error": r.get("error"), "seconds": r["seconds"],
                      "verdicts": [f"{v['commitment']}:{v['status']}" for v in last]}, indent=1))  # fmt: skip


if __name__ == "__main__":
    main()
