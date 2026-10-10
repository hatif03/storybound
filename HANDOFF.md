# HANDOFF: continue building from Claude Code in this folder

Written 10 Oct 2026, ~14:30 IST, at the end of the session that was run from `D:\neatlogs`. Read `CLAUDE.md` (rules) and `docs/DESIGN.md` (design) first. This file says where things stand and what to do next.

## Why this folder matters for Entire
Entire records a session only if Claude Code is started inside this repo. Everything before this point was built from outside it, so there are **0 Entire checkpoints** (`entire status`, `entire checkpoint list`). From now on: work here, commit often, let Entire link checkpoints (`commit_linking: always`). Also run `entire login`.

## What exists
| Area | State | Where |
| --- | --- | --- |
| Oath engine (M2) | done, 53 tests | `src/storybound/oath/` |
| LangGraph pipeline, arms B0 (single shot), B1 (gated, pipelined review with rollback), B2 (same model reviews its own story) | done | `src/storybound/pipeline.py`, `agents/` |
| FastAPI API | done, matches `docs/API.md` | `src/storybound/api.py` |
| Web app | built (React + Vite + Rive, mock mode `?mock=1`), not yet run against a real story | `web/`, `docs/WEB.md` |
| Evidence tools | ledger, sweep, report, judge eval, safety eval, linter, `EVIDENCE.md` generator | `scripts/`, `evidence/` |
| Platforms log | per-platform state | `docs/PLATFORMS.md` |
| Build log | dated entries | `hackathon.md` |
| Assets, brand, fonts, owl poses, audio | copied in | `assets/` (inventory: `assets/README.md`) |
| Launch motion-graphic (89 s draft) | sources copied; paths fixed | `video/launch/` (`npm install`, then `node render.mjs`) |
| Planning docs | `docs/planning/*.md` (pitch, content calendar, neatlogs, entire, cfo, frontend, crustdata) | kept for reference |
| Sister's real drawings | **private, gitignored** | `_private/demo-drawings/` (never commit, never put in traces or posts) |
| Old project folders | local only, gitignored | `_reference/` (do not read from, do not mention) |

## Measured so far (all in `evidence/`)
- Baseline sweep `sweep-1-p1` (prompt p1, code a19c731, 55 runs): ungated shipped a broken promise in 28/28 stories (206 broken, 96 of them reading level); gated in 7/24 (13 broken); 3 gated runs errored from bugs that are now fixed. Report: `evidence/reports/*sweep-1-p1.md`.
- Safety screen over 26 fixture drawings: 25/26 matched; 1/1 unsafe refused; 0 benign refused.
- Judge with injected faults: 24/24 caught, 0/8 clean flagged, 0/88 unverifiable.
- A real recovery run (image quota 429, pages degraded to text only, receipt said so): trace `94db23729dac6323368749acba4be1cb`.
- neatlogs detections: "Oath violation", "Critical safety stop" (free plan has 5 slots, 3 defaults exist).
- Entire graph outputs: `evidence/entire/`.

## Running when this was written (check before starting anything)
- `sweep-2-p2` (prompt p2, pipelined loop, arms B0, B1, B2; 84 runs, about 12 done): `scripts/sweep.py`. Check with Task Manager (a `python.exe` running `sweep.py`) before re-launching, to avoid duplicates. It is resumable: finished jobs are in `evidence/ledger.jsonl` and are skipped.
  `.venv\Scripts\python.exe scripts\sweep.py --name sweep-2-p2 --arms B0,B1,B2 --fixtures benign/bunny-bow-carrot,benign/rhinoceros-crayon,benign/van-crayon,benign/christmas-tree-digital,tier-b-text/fish-kill-fish-caption,tier-b-text/injection-ignore-instructions,edge/copyrighted-character-mickey-1928 --lessons sharing,honesty --k 2 --workers 5`
- Dev API server on port 8000: `.venv\Scripts\python.exe -m uvicorn storybound.api:app --app-dir src --port 8000`. Restart it after `npm run build` in `web/` so it serves the app at `/`.
- `evidence/ledger.jsonl` grows as the sweep runs: commit it.

## Next steps, in order
1. When sweep 2 finishes: `python scripts/report.py --name sweep-2-p2`. Write `evidence/hardening/HR-001.md` (reading level: prompt p1 to p2) and `HR-002.md` (latency: pipelined review, planner beside the oath author; compare seconds and `first_page_s`). Required headings: Trigger, Diagnosis, Change (commit sha, Entire checkpoint, prompt version), Before, After, Regression fixture. Link the neatlogs trace ids. Include B2 (self-critique) honestly in the comparison, even if it narrows our lead.
2. Run one real story through the web UI (media on) and fix what breaks. Not yet verified: real pictures and narration in the reader, touch devices, Safari, screen reader.
3. Backend items still open: a delete endpoint ("forget this story"); the hardening candidate where a text-only fixture flips between sanitise and ask-redraw.
4. cfo.ai: sign in through the MCP prompt in this session, then build the plan from measured cost per story (neatlogs analytics; our estimate in `budget.usd_estimate` is labelled an estimate). Save evidence to `evidence/cfo/`. Draft inputs: `docs/planning/cfo.md`.
5. Crustdata: key is in `.env` (CRUSTDATA_API_KEY, tested, 5200 credits). Use it for the market and competitor notes in the cfo.ai model. **Raw Crustdata data must not go in the public repo**: keep derived figures only, cited "Crustdata, <date>".
6. Parent/teacher-written promises (free-text promises that become judged `lesson_specific_*` commitments): small, and a real differentiator. Optional: a short animated clip per page.
7. Demo video (at most 3 minutes; neatlogs, Entire, cfo.ai each on architecture, implementation, runtime, reasoning, result) and the #neatHack posts (`docs/planning/content.md`, log real ones in `evidence/posts.md`). Final: `python scripts/build_evidence.py`, `python scripts/lint_evidence.py`, publish the repo, quote-post on X Monday 12 Oct 19:00-23:55 IST.

## Things to remember
- Keys live only in `.env` (gitignored). Never print them, commit them, or put them in prompts. Rotate all pasted keys (neatlogs, AWS, K2, Crustdata) after the hackathon.
- Commit trailer: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Use plain `date` for IST. For big files use the Write tool, not bash heredocs.
- AWS: no Bedrock/Polly/S3; we do not host on AWS (it would need a Google credential on the box).
- The neatlogs MCP is reachable through `scripts/neatlogs_mcp.py`; once the repo's `.mcp.json` servers load in this session, use them directly (neatlogs, cfo.ai, Crustdata).
