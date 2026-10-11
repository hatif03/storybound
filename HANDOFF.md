# HANDOFF: where things stand

Refreshed Sun 11 Oct 2026, morning IST. Read `CLAUDE.md` (rules), then [docs/STATUS.md](docs/STATUS.md) (done and left, with who must act), [docs/PROCESS.md](docs/PROCESS.md) (how we got here) and [docs/TOOLS.md](docs/TOOLS.md) (neatlogs, Entire, cfo.ai).

## State in five lines
1. The product works end to end through the real browser UI: draw, lesson, optional grown-up promises, 8 verified pages with pictures and narration, a verified quiz and a picture-order game, a read-along movie, a grown-ups receipt, and a Forget that deletes on the server.
2. Evidence: sweeps 1 to 7 in `evidence/ledger.jsonl`, six hardening records (HR-001 to HR-006) plus HR-007 below, exported traces, screenshots, story packages, Entire and cfo.ai outputs. `EVIDENCE.md` is generated: `python scripts/build_evidence.py` then `python scripts/lint_evidence.py`.
3. Tests: 80 backend (`pytest tests`), 19 web (`cd web; npm run test`); both green at the last commit.
4. All work is committed locally on `main` (37+ Entire checkpoints). Not everything is pushed.
5. **The demo video is not made yet** (the builder asked for it last). The video agent can generate it from the final ledger: see "Demo video" below.

## Do these before anything else (only the builder can)
- **Rotate the neatlogs key and the hackathon gateway key.** Both were pasted into the session and are inside Entire checkpoint transcripts, some already on the private `origin`. Do not make the repo public before deciding what to do about those checkpoint refs (Entire documents no removal of a pushed checkpoint).
- **Entire Trails:** install the Entire GitHub App on `hatif03/storybound` and select the repo on entire.io. Until then `entire trail create` and `entire review` answer "repository not found". Runners are already scaffolded in `.entire/runners/`.

## What is running / how to start things
- Dev server: `.venv\Scripts\python.exe -m uvicorn storybound.api:app --app-dir src --port 8000` (serves the API and `web/dist`; restart after backend changes; rebuild the web app with `cd web; npm run build`).
- A real story through the real UI: `node web\scripts\e2e-real.mjs` (about $0.40 plus $0.04 for the movie, about 13 minutes). Free demo-mode check of the quiz and game: `node web\scripts\e2e-quiz-mock.mjs`.
- Check what an anonymous visitor sees on a share link: `node web\scripts\check-share-link.mjs <url> <out.png>`.

## Keys and environment
Keys live only in `.env` (gitignored): Vertex through `gcloud` credentials, `IFM_API_KEY` (K2), `LITELLM_API_KEY` and `LITELLM_BASE_URL` (hackathon gateway), `NEATLOGS_API_KEY`, `NEATLOGS_PROJECT_ID`, `CRUSTDATA_API_KEY`. To let Claude Code's neatlogs MCP see the key, start it from `scripts\dev-shell.ps1`. The neatlogs CLI is signed in through device login (read-only scopes); the cfo.ai and Crustdata MCPs are authorised.

## Demo video (last step)
`python scripts/make_video.py --brief "..." --claims video/harness/claims/preview.json --title demo --out evidence/video/demo --name video-demo` plans from a brief and a claim catalogue; every number comes from an evidence file; `requires_coverage` makes the video oath demand each tool on architecture, implementation, runtime, reasoning and result (15 tags). Extend the claim catalogue with the final numbers (HR records, cost, margin) and the ledger counts first. The script is in `docs/planning/pitch.md` section 6. Keep the result at 3:00 or less; the harness refuses longer.

## Things to remember
- Commit trailer: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. One intent per commit. For big files use the Write tool, not shell heredocs.
- Never print, commit or paste a key. Real drawings stay in `_private/`.
- AWS is not used (no Bedrock, Polly or S3 in the account).
- `evidence/runs/` is gitignored but earlier files are tracked; add new ones with `git add -f`.
