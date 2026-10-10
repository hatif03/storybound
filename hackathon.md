# hackathon.md: neatHack build log

Kept in the format of the neatHack `neathack` skill. Only sanitized, shareable evidence is linked here: no keys, no `.env` contents, no personal data, no private traces. Planned and completed work are kept apart; only tests that actually ran are recorded.

## Project
**Storybound**: a children's (age 4-8) storybook agent. A drawing and a lesson go in; the agent writes an *oath* (what it owes the child), writes and checks each page against it before the child sees it, repairs pages that break it, and ships a *receipt*. Planning documents (written 9-10 Oct, before the window, no application code) are in `docs/planning/`; the decisions of 10 Oct are at the top of `docs/planning/plan.md`.

## Team
Solo builder. AI coding help: Claude Code (checkpointed by Entire).

## Stack
- Orchestration: LangGraph (no Google ADK). API: FastAPI. Python 3.12.
- Models: Gemini on Google Vertex AI (writer, vision, image, speech) and K2 Horizon (independent judge). AWS is hosting only (no Bedrock or Polly in the hackathon account).
- Observability: neatlogs (project `482c3038-22f9-49e6-8938-e816ce252f75`). Coding-agent memory: Entire (checkpoints, graph). Business plan: cfo.ai. Market data: Crustdata (never in the public repo).
- Design lineage: Storytopia (Lighthouse) and Sworn (Agentic Contract Framework), both MIT; code is re-written, not copied; sample drawings and lesson data reused with the organizers' approval.

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

(Next entries are appended after each work session.)

## Demo
Planned: a 3:00 video covering neatlogs, Entire and cfo.ai on architecture, implementation, runtime, reasoning and result; recovery and repair runs on camera; a family-friendly demo with a parent's consent. Not started.

## Known limitations and next steps
- Entire login, Trails access (form) and the GitHub App import are manual steps for the builder.
- cfo.ai and Crustdata MCP sign-in need an interactive session.
- K2 judge is a reasoning model: expect higher latency and token use.
- The judge is a different family from the writer only because of K2; Claude on Vertex has no quota.
- Free neatlogs plan limits (100k spans, 5 detectors, 14-day retention) may apply; traces are exported into `evidence/traces/` as we go.

## Submission
Not yet. Window: Mon 12 Oct 19:00-23:55 IST, by quote-posting the official neatlogs post on X. Checklist lives in `docs/planning/plan.md` section 10.4 and `EVIDENCE.md`.
