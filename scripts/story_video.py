"""Make a read-along video from a story package (a run folder with story.json, drawing and page media).

python scripts/story_video.py evidence/stories/<name> [--name ledger-name]
Writes <package>/video/ (spec, receipt, video.mp4).
"""

import os

os.environ["NEATLOGS_WORKFLOW"] = "make-video"  # before the tracing module initialises neatlogs

import argparse  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from storybound.video import agent, story  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("package")
    ap.add_argument("--name", default="")
    ap.add_argument("--max-repairs", type=int, default=agent.MAX_REPAIRS)
    a = ap.parse_args()
    pkg = Path(a.package).resolve()
    r = agent.make(story.build_spec(pkg), title=pkg.name, out=pkg / "video", max_repairs=a.max_repairs, name=a.name)
    last = r["attempts"][-1]["verdicts"] if r.get("attempts") else []
    print(json.dumps({"outcome": r.get("outcome"), "trace_id": r.get("trace_id"), "repairs": r["repairs"], "broken": r.get("broken"),
                      "video": r.get("video"), "error": r.get("error"), "seconds": r["seconds"],
                      "failed": [f"{v['commitment']}:{v.get('scene')}" for v in last if v["status"] != "pass"]}, indent=1))  # fmt: skip


if __name__ == "__main__":
    main()
