# hackathon.md: neatHack build log

Kept in the format of the neatHack `neathack` skill. Only sanitized, shareable evidence is linked here: no keys, no `.env` contents, no personal data, no private traces. Planned and completed work are kept apart; only tests that actually ran are recorded.

## Project
**Storybound**: a children's (age 4-8) storybook agent. A drawing and a lesson go in; the agent writes an *oath* (what it owes the child), writes and checks each page against it before the child sees it, repairs pages that break it, and ships a *receipt*. Planning documents (written 9-10 Oct, before the window, no application code) are in `docs/planning/`; the design is in `docs/DESIGN.md`.

## Team
Solo builder. AI coding help: Claude Code (checkpointed by Entire).

## Stack
- Orchestration: LangGraph (no Google ADK). API: FastAPI. Python 3.12.
- Models: Gemini on Google Vertex AI (writer, vision, image, speech) and K2 Horizon (independent judge). AWS is hosting only (no Bedrock or Polly in the hackathon account).
- Observability: neatlogs (project `482c3038-22f9-49e6-8938-e816ce252f75`). Coding-agent memory: Entire (checkpoints, graph). Business plan: cfo.ai. Market data: Crustdata (never in the public repo).
- Code written during the window; sample drawings and lesson data used with the organizers' approval.

## Build log

### 2026-10-10, before kickoff (12:30 IST): setup only, no application code
- 12:09 Workspace checked. Today's rules re-read. Repo created at `D:\storybound` (`git init`, **no commits before kickoff**).
- 12:12 AWS CLI profile `neathack` created (keys stored in `~/.aws`, not in the repo). Identity verified. **Bedrock, Polly, S3, IAM-read all denied** for this user; the organisers' guide confirms only EC2, Lambda, IAM roles and load balancers, us-east-1, $25 team allowance. Another team's EC2 instance and Lambdas are visible in the account and are not to be touched.
- 12:16 Vertex AI verified in GCP project `project-f0b6b4ce-541f-43ff-9f7`: Gemini text (3.7-flash, 3.1-pro-preview, 3.1-flash-lite), Gemini image (3.1-flash-image, 2.5-flash-image), Gemini TTS (gemini-2.5-flash-tts) all answered. Claude on Vertex: zero quota. Llama and Mistral: not enabled.
- 12:19 K2 Horizon (`IFM/K2-Horizon-375B-A23B`, `https://api.ifm.ai/v1`) verified with a one-line chat call. Chosen as the independent judge.
- 12:20 neatlogs: CLI 0.2.0 installed; SDK 1.4.26 in a Python 3.12 venv; skills `neatlogs-py`, `neatlogs-py-langchain`, `neatlogs-public-api-cli` installed (reviewed, clean); `doctor --local` pass; `doctor --probe` pass (8/8); probe trace `9c1a84ae1026086343ff64eb2e1208b3` found again through MCP `search_traces` and `get_trace_context`. Files: `evidence/setup/20261010-1223-IST-*`.
- 12:21 Entire 0.11.4 installed and enabled for Claude Code (9 hooks); `commit_linking: always`; entire-graph 0.4.0 installed and initialised (local only, no network egress).
- 12:24 Crustdata CLI 0.2.19 installed (not logged in: needs the API key or a browser sign-in).
- MCP configs prepared for Claude Code (`.mcp.json`) and Cursor (`.cursor/mcp.json`): neatlogs (key from the environment), cfo.ai (OAuth), Crustdata (OAuth). No secret is stored in either file.
- Setup files prepared before kickoff: `CLAUDE.md`, `AGENTS.md`, `.gitignore`, `.env.example`, MCP configs, `scripts/dev-shell.ps1` (a 20-line helper that loads `.env`). They contain no application logic.

### 2026-10-10, kickoff 12:30 IST
- 12:30 **First commit** `03f9586` at 12:30:17 IST (setup files only, no application code). 12:30 GitHub repository `hatif03/storybound` created **private** (publish later with one command, see `docs/setup/SETUP.md`); history pushed. Note: commit `0b526c2` message says "storybond", a typo corrected one minute later in `591e717`; history is not rewritten.
- 12:37 **Entire Brain** installed by hand from the v0.1.0 Windows release (checksum verified), set up with `--no-backfill --no-daemon`, agent guide written, six durable project rules stored with explicit paths (no model calls). Commit `1f687f4`. No `Entire-Checkpoint` trailer yet: this planning session is not rooted in the repo, so Entire has no session to link; checkpoints start with the first Claude Code session started from `D:\storybound`.
- Launch video (a motion graphic from the demo drawings and brand assets, scratch voice-over by Gemini TTS) built outside the repo in `D:
eatlogs\launch-video`.

### 2026-10-10, 12:40-13:00 IST: M1, scaffold and first real calls
- 12:48 Commit `4bfc19b`: ground-up design document (`docs/DESIGN.md`), old planning copy removed, links repointed, local reference folder gitignored.
- 12:52 Commit `cf5b7d9`: Python package (`src/storybound`), config (models, thresholds, budget in one file), Gemini and K2 clients with retry and typed errors, neatlogs wrapper that degrades to a no-op, evidence ledger, 9 unit tests green, ruff clean.
- 12:55 Spikes run against the real services, four traces read back through the neatlogs MCP server: Gemini text, Gemini vision on a sample drawing, K2 judge with a verbatim-quote check, and a GUARDRAIL span nested under a WORKFLOW root. Files: `evidence/spikes/`, `evidence/traces/`.
- Found by running it: Gemini 3 thinking tokens count against `max_output_tokens` (a 200-token cap returned 8 words); the client now adds headroom and refuses output that stopped at the cap. neatlogs cost for Gemini excludes thinking tokens; K2 shows no cost.

### 2026-10-10, 13:00-13:30 IST: M2 oath engine, M3 pipeline and API
- 13:07 Commit `5b709a6` (M2): one verdict object for every check; 19 commitments (core fixed, additions only as `lesson_specific_*`, hashed); deterministic verifiers first, seeded judge sampling (safety always 1.0), K2 judge with a verbatim-quote check done in code; safety fails closed, quality fails open as a flagged warning; coverage report. 37 offline tests.
- 13:18 Commit `8010a00` (M3a): LangGraph pipeline (safety, character card, oath author, planner, write/verify/repair/regen loop, story gate, media, receipt) and the observe-only arm B0. **First full real run** (bunny, sharing, gated arm, judge on): 8 pages, every page failed `age_reading_level` on the first pass and was repaired once, one page tripped `story_safe_text` ("fighting") in an earlier no-judge run and was regenerated; 0 broken promises shipped; 313 s; trace `301911c89d3eb42738c51022ab863a22` (39 LLM calls, measured $0.0255 against an estimate of $0.0144: thinking tokens). File: `evidence/runs/20261010-1318-IST-bunny-sharing-B1-first-full-run.json`.
- 13:20 Safety screen run over all 26 fixture drawings: 24/26, then 25/26 matched; the one unsafe drawing refused (1/1); no benign drawing refused. Two expectations in my own fixture file were wrong (a name or place written on a drawing is a personal detail, so Tier B is right) and were corrected; one text-only fixture flips between sanitise and ask-redraw at temperature 0 (logged for hardening). Files: `evidence/runs/*safety-eval*`.
- 13:22 Commit `283a4cf` (M3b): FastAPI app matching `docs/API.md`; 48 tests.
- 13:24 Real picture (15 s, 2 MB PNG, re-encoded to a small JPEG for the web) and real narration (11 s, mp3) generated and checked. Entire graph search and diff outputs saved in `evidence/entire/`.
- 13:27 Baseline sweep `sweep-1-p1` started (56 runs: 7 drawings x 2 lessons x 2 seeds x 2 arms, prompt version p1). The front end is being built in parallel in `web/`.
- Honest gap: the sessions that wrote these commits were not rooted in the repo, so no Entire checkpoint is linked to them yet.

(Next entries are appended after each work session.)

### 2026-10-10, 14:20-15:30 IST: sweep 2, hardening records HR-001 and HR-002
- 14:18-15:04 `sweep-2-p2` (prompt p2, arms B0/B1/B2, 84 jobs, 0 errors). Shipped with a broken promise: B0 27/28, **B1 0/28**, B2 27/28. The model reviewing its own story (B2) did not narrow the gap. Report: `evidence/reports/*sweep-2-p2.md`. Cost per story (estimates): B0 $0.0083, B1 $0.0162, B2 $0.0198.
- The sweep-1 report had been written before the last sweep-1 job finished (14:20); regenerated from the final ledger (B1 shipped broken 8/25, not 7/24) and the stale copy removed.
- HR-001 (reading level, p1 to p2): hypothesis was that the writer was never told the word limit the check enforces. B0 (control, no other change) pages over the limit on the first pass 42.9% to 1.8%; B1 90.5% to 9.8%. B1's page-by-page writer still overshoots by about a word (trace `a32498d665231ab02f7218b8b54e9a3f`, scene 7: 15 words against 14); untested idea for HR-003: aim under the limit. Regression test added (58 tests pass). Record: `evidence/hardening/HR-001.md`.
- HR-002 (latency, pipelined review): the sweep-1 to sweep-2 comparison is confounded by HR-001, so I ran an ablation: same 14 jobs, `STORYBOUND_MAX_AHEAD=1` (sequential) against the sweep-2 rows. Total time per story 230.6 s to 149.6 s mean (207.8 to 122.0 median), faster on 11 of 14 jobs; time to first page did **not** improve (median 45.8 s sequential, 61.7 s pipelined). Small sample, sampled outputs, estimated cost. Record: `evidence/hardening/HR-002.md`.
- Seen, not fixed: the reading-level check counted "peach-colored" as one long word on one shipped-with-notes story (possible false positive).
- Entire: first checkpoints exist for commits made in this repo (`bcdd0c4`, `7a13f29`, `0ad1832`, `55ccd97`). The change commits `04ffebb` and `daec9ea` were made outside the repo and have none; the records say so.
- neatlogs: the MCP in `.mcp.json` fails with 401 in the VS Code session because `NEATLOGS_API_KEY` is not in that process's environment; traces were read through `scripts/neatlogs_mcp.py` (key from `.env`). cfo.ai and Crustdata MCP connected after approval.
- Tests that ran: `pytest tests` (58 passed), `ruff check` clean.

## Demo
Planned: a 3:00 video covering neatlogs, Entire and cfo.ai on architecture, implementation, runtime, reasoning and result; recovery and repair runs on camera; a family-friendly demo with a parent's consent. Not started.

## Known limitations and next steps
- Entire login, Trails access (form) and the GitHub App import are manual steps for the builder.
- cfo.ai and Crustdata MCP sign-in need an interactive session.
- K2 judge is a reasoning model: expect higher latency and token use.
- The judge is a different family from the writer only because of K2; Claude on Vertex has no quota.
- Free neatlogs plan limits (100k spans, 5 detectors, 14-day retention) may apply; traces are exported into `evidence/traces/` as we go.

## Submission
Not yet. Window: Mon 12 Oct 19:00-23:55 IST, by quote-posting the official neatlogs post on X. Checklist lives in `EVIDENCE.md` and the linter.
