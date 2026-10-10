# evidence/: the trail that lets a judge check every claim

Everything here is created as we go. The generated `EVIDENCE.md` at the repo root is rendered from `ledger.jsonl` and these folders.

| Folder or file | What goes in it | Naming |
| --- | --- | --- |
| `ledger.jsonl` | one JSON line per named run: UTC and IST time, git sha, fixture, arm, prompt versions, neatlogs trace id, outcome, per-commitment verdicts, repairs, tokens, cost, latency | append only |
| `traces/` | exported neatlogs traces (`neatlogs traces export <id> --format markdown` and `--format json`), sanitized | `YYYYMMDD-HHMM-IST-<what>-<traceid8>.md/json` |
| `screens/` | screenshots of traces, detections, alerts, Investigate, analytics, the app, the cfo.ai page, Entire output | `YYYYMMDD-HHMM-IST-<what>.png` |
| `entire/` | pasted CLI output: `entire checkpoint explain`, `entire graph diff`, `graph checkpoint`, `graph verify`, `entire status --detailed` | `YYYYMMDD-HHMM-IST-<command>.txt` |
| `cfo/` | shared page link, screenshots, Version history, the xlsx download | |
| `hardening/` | one record per real failure: trigger trace, diagnosis, change (sha, checkpoint id), regression fixture, proof (before and after) | `HR-001.md`, ... |
| `setup/` | the setup read-backs (doctor output, MCP whoami and search) | |
| `posts.md` | every `#neatHack` post: URL, time, what it shows | |

## Rules
1. **Time zone:** the machine clock is IST. In Git Bash use plain `date`, never `TZ=...` (it silently returns UTC). Name files with the IST time.
2. **Capture while it is fresh.** After each named run: ledger line, trace export, screenshot, and one line in `hackathon.md`.
3. **Triples:** for each key commit record (git sha, `Entire-Checkpoint` id, neatlogs trace id).
4. **Before and after:** an "agent improved" claim needs both runs, the numbers compared, the commit, the checkpoint and both trace ids.
5. **Sanitize:** no keys, no `.env`, no personal data, no real child's drawing, no Crustdata records. Fixtures only.
6. **Retention:** free-plan traces expire; the repo copies are the record.
