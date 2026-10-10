"""Minimal neatlogs MCP client for evidence readback (no secrets printed).

Usage:
  python scripts/neatlogs_mcp.py tools
  python scripts/neatlogs_mcp.py call search_traces '{"query": "spike"}'
  python scripts/neatlogs_mcp.py call get_trace_context '{"trace_id": "<id>"}' [--save name]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from storybound import ledger  # noqa: E402
from storybound.config import env  # noqa: E402

URL = "https://ingest.neatlogs.com/mcp"


def _post(payload: dict, session: str | None = None) -> httpx.Response:
    headers = {
        "Authorization": f"Bearer {env('NEATLOGS_API_KEY')}",
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }
    if session:
        headers["Mcp-Session-Id"] = session
    r = httpx.post(URL, json=payload, headers=headers, timeout=60)
    if r.status_code >= 400:
        sys.exit(f"HTTP {r.status_code}: {r.text[:300]}")
    return r


def _body(r: httpx.Response) -> dict:
    body = r.text
    if "data:" in body:
        body = next(line[5:].strip() for line in body.splitlines() if line.startswith("data:"))
    return json.loads(body) if body.strip() else {}


def rpc(method: str, params: dict | None = None) -> dict:
    init = _post(
        {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "storybound-evidence", "version": "0.1"},
            },
        }
    )
    sid = init.headers.get("mcp-session-id")
    _post({"jsonrpc": "2.0", "method": "notifications/initialized"}, sid)
    return _body(_post({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}, sid))


def main(argv: list[str]) -> None:
    if not argv:
        sys.exit(__doc__)
    if argv[0] == "tools":
        out = rpc("tools/list")
    else:
        out = rpc("tools/call", {"name": argv[1], "arguments": json.loads(argv[2]) if len(argv) > 2 else {}})
    text = json.dumps(out, indent=2, ensure_ascii=False)
    if "--save" in argv:
        name = argv[argv.index("--save") + 1]
        p = ROOT / "evidence" / "traces" / f"{ledger.stamp(name)}.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        print("saved", p.relative_to(ROOT))
    else:
        print(text[:6000])


if __name__ == "__main__":
    main(sys.argv[1:])
