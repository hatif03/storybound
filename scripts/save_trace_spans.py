"""Save every span of one neatlogs trace through the MCP (project key; no sign-in needed) and count what matters for HR-016.

  python scripts/save_trace_spans.py <trace_id> <out.json>

The trace export endpoint and the CLI sign-in are not needed. The MCP pages 50 spans at a time and may answer 429 for a minute under load.
"""

from __future__ import annotations

import collections
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import neatlogs_mcp as m  # noqa: E402


def fetch(trace_id: str) -> dict:
    spans: list[dict] = []
    off = 0
    meta: dict = {}
    while True:
        try:
            r = m.rpc("tools/call", {"name": "get_trace_context", "arguments": {"trace_id": trace_id, "offset": off}})
        except SystemExit:  # the helper exits on HTTP 429 (capacity); wait the 81 s it asks for
            time.sleep(85)
            continue
        text = "".join(c.get("text", "") for c in r.get("result", {}).get("content", []))
        try:
            j = json.loads(text)
        except ValueError:
            time.sleep(60)
            continue
        if "spans" not in j:
            time.sleep(60)
            continue
        meta = {k: v for k, v in j.items() if k != "spans"}
        spans += j["spans"]
        if j.get("next_offset") in (None, off) or len(spans) >= j.get("span_count", 0):
            return {**meta, "spans": spans}
        off = j["next_offset"]


def main() -> None:
    tid, out = sys.argv[1], Path(sys.argv[2])
    d = fetch(tid)
    out.write_text(json.dumps(d, indent=1), encoding="utf-8")
    names = [s["name"] for s in d["spans"]]
    c = collections.Counter(n.split(":")[0] + (":" + n.split(":")[1] if n.startswith("verify:image") else "") for n in names if n.startswith(("illustrate", "verify:image")))
    print(f"{len(names)} spans of {d.get('span_count')}; illustrate={sum(n == 'illustrate' for n in names)}; picture checks={sum(n.startswith('verify:image') for n in names)}; {dict(c)}")


if __name__ == "__main__":
    main()
