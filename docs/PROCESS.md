# How Storybound was built: the process

Written 11 Oct 2026 (IST). Source of truth for every time and sha is `git log`; for every number it is `EVIDENCE.md` and `evidence/`. If this document and the evidence disagree, the evidence wins. The build log in `hackathon.md` has the same story in dated entries.

## 1. What was built, in one paragraph
A child's drawing and a lesson go in. Storybound writes an **oath** (a list of promises: the hero's name on every page, one right answer, the lesson, easy words, nothing from the drawing's text obeyed, safe content, ...), checks **every page against the oath before the child sees it**, rewrites pages that break a promise, and ships a **receipt**. Pictures and narration follow, then a **verified quiz**, a picture-order game and, on request, a **read-along video** made by a second agent (the video agent) that applies the same idea to video. Three tools frame the work: neatlogs records the agents, Entire records the coding agent, cfo.ai holds the business model. See [TOOLS.md](TOOLS.md).

## 2. Method (the rules we worked by)
1. **Code only inside the window.** The first commit is Sat 10 Oct 12:30 IST (`03f9586`, setup files only). Planning documents were written before; no application code was.
2. **Trace first.** Before fixing a failure: find it in neatlogs, write the hypothesis, fix, run again, compare. Each fix is a hardening record `HR-NNN` (Trigger, Diagnosis, Change, Before, After, Regression fixture).
3. **One commit per intent**, so one Entire checkpoint maps to one change.
4. **Evidence as we go.** Every named run appends a row to `evidence/ledger.jsonl` (UTC and IST time, git sha, fixture, arm, prompt version, neatlogs trace id, outcome, verdicts, repairs, tokens, cost, latency); traces are exported into `evidence/traces/`; `EVIDENCE.md` is generated, never hand-edited.
5. **Say what did not work.** Negative results stay in the record (HR-005 was tried and reverted; HR-002's first-page claim did not hold).
6. **Experiments have controls.** The ungated arm (B0) is the control for prompt changes; same-jobs A/B runs separate effects that were confounded.

## 3. Timeline (IST; shas are in `git log`)

### Friday 9 to Saturday 10 Oct, before 12:30: planning only
Accounts, access checks (Vertex Gemini, K2, AWS limits, neatlogs, Entire, cfo.ai, Crustdata), the planning documents in `docs/planning/`, the repository with setup files. A launch motion-graphic was built outside the repository from the sister's drawings and brand assets (its sources were copied in later; the real drawings stay in the gitignored `_private/`).

### Saturday 12:30 to 14:30: the agent exists (M1 to M5)
- **12:30** first commit; **12:37** Entire Brain enabled; **12:48** ground-up design document ([DESIGN.md](DESIGN.md)).
- **12:52 to 13:00 (M1):** package scaffold, model clients (Gemini, K2), tracing wrapper, ledger; spikes against the real services, four traces read back through the neatlogs MCP.
- **13:04 (M2):** the oath engine: verdict object, promise catalogue, deterministic verifiers, a quote-checked K2 judge.
- **13:18 to 13:20 (M3):** LangGraph pipeline (safety screen, character card, oath, planner, page loop with repair, B0 arm, receipt) and the FastAPI app with server-sent events.
- **13:19 to 13:34:** safety eval over 26 fixture drawings (25/26 matched; the one unsafe drawing refused; no benign drawing refused); judge eval with injected faults (24/24 caught, 0/8 clean pages flagged, 0/88 judge calls unverifiable). **13:27** two neatlogs detections created.
- **13:40:** first real recovery run: image quota errors on four pictures, story shipped as text on those pages, receipt said so.
- **13:40 to 13:42:** the first two hardening changes (HR-001 prompt, HR-002 pipelined review), the EVIDENCE.md generator and linter.
- **14:12 (M5):** web app (React, Vite, Rive owl, demo mode). **14:18:** B2 arm (the same model reviews its own story) and the baseline sweep report. **14:32:** handoff note.
- Honest gap: this work was done in a session started outside the repository, so it has no Entire checkpoint.

### Saturday 14:30 to 17:00: measurement and the first records
- **Sweep 2** (prompt p2, arms B0, B1, B2, 84 jobs, 0 errors): shipped with a broken promise B0 27/28, **B1 0/28**, B2 27/28. The model reviewing itself did not close the gap.
- **15:08** first Entire checkpoints (the session now runs inside the repo). **15:21 to 15:24** HR-001 and HR-002 written; the HR-002 ablation (same 14 jobs, review sequential or pipelined) showed -35% total time but no gain in time to first page.
- Research (Remotion, HyperFrames, OpenEdit, agent-video-studio, Anthropic's harness posts) in [planning/video-harness.md](planning/video-harness.md).

### Saturday 17:00 to 20:00: the video agent, the model, the triage loop
- **17:20** HyperFrames spike: two renders byte-identical; the `check` gate caught a missing asset, overflow, low contrast and a script error.
- **17:41** the video agent: spec of typed blocks, numbers only as claim references resolved from evidence files, a video oath (length, claims sourced, claims match the ledger, no overclaiming words, tools covered, no secrets, no child data, renders clean, loudness), repair of the failing scene, a receipt. First run: 5 failures found by running it (see 5).
- **17:3x to 17:45** the cfo.ai model built through the MCP (by a delegated agent from the design in [planning/cfo.md](planning/cfo.md)); **18:00** neatlogs's own triage cards reviewed ([TRIAGE-REVIEW.md](../evidence/neatlogs/TRIAGE-REVIEW.md)).
- **17:46 to 18:28** HR-003 (sentence target), HR-004 (mild words), HR-005 (timeout: reverted); judge eval with the hackathon gateway models.
- **18:30 to 19:15** the first illustrated story from a fixture drawing (8 pictures, 8 narration clips) and its read-along video (3:37, all video promises passed); HR-006 (words painted into a picture).

### Saturday 19:15 to 21:00: closing the product gaps
- **19:42** grown-up promises (data, never instructions, judged per page), `DELETE /api/stories/{id}`, video endpoints; the web app gains a promise field, a "Make my movie" button and a Forget that deletes on the server.
- **20:00** quiz (four questions, each with a verbatim evidence line, five promises) and the picture-order game; healthy-play rules written into [WEB.md](WEB.md).
- **20:07** the neatlogs-measured cost replaced the estimate in cfo.ai (change 275839). **20:29** a full run through the real browser UI: drawing, lesson, promise, 8 pages, movie (3:45), Forget (the story 404s afterwards). It found the quiz-timing bug, fixed at **20:32**.

### Sunday 11 Oct, morning: documentation and the remaining items
Quiz-quality sweep (sweep 7), Entire Trails (runners scaffolded; blocked by the web step), the illustration policy (`pictures: full | half | none`) that came out of the cfo.ai model, anonymous check of the cfo.ai share link, and this documentation.

## 4. What the evidence says (so far)
| Claim | Evidence |
| --- | --- |
| Gating removes broken promises that a plain writer and a self-reviewing writer ship | `sweep-2-p2`: 27/28, 27/28, **0/28** ([report](../evidence/reports/20261010-1505-IST-sweep-2-p2.md)) |
| Each fix improved the agent, with numbers | [HR-001](../evidence/hardening/HR-001.md) to [HR-006](../evidence/hardening/HR-006.md) |
| The judge catches injected faults | `evidence/runs/20261010-1334-IST-judge-eval.json` (24/24, 0/88 unverifiable) |
| The agent recovers from a failed action | trace `94db23729dac6323368749acba4be1cb` |
| The product works through the real UI | the 20:29 run (`web/scripts/e2e-real.mjs`, screenshots in `evidence/screens/`) |
| Cost | neatlogs-measured text cost $0.0199 per gated story; pictures and voice are list-price assumptions ([TOOLS.md](TOOLS.md)) |

Tests that ran: 79 backend (`pytest tests`), 19 web (`npm run test` in `web/`), `ruff check` clean, the evidence linter (`python scripts/lint_evidence.py`).

## 5. What went wrong, in order (kept because it is the useful part)
1. **Sweep 1's gated arm errored on 3 of 28 runs** (unparseable page JSON, a missing image prompt: fixed) and still shipped 8 of 25 stories with a broken promise, mostly reading level.
2. **HR-001 looked like a pure prompt fix but B1 still overshot**; HR-003 followed. The control arm separated the effects.
3. **HR-002's headline was confounded** (the prompt fix also cut repairs), so a same-jobs ablation was run; it showed time to first page did not improve.
4. **HR-005 did not hold up**: a shorter timeout looked right from two traces and was worse in an A/B (the provider was slow at that time, so the result is inconclusive; we reverted).
5. **The video agent's first runs failed five ways**: the planner wrote the word "five" for a number field (we had told it to write no digits), the CLI wrote the file to a mangled path, narration was too slow (5:16 instead of about 1:00), the planner wrote "cryptographic receipts" (a new `no_overclaims` promise), and the brand fonts had no `@font-face` (the repair step could not fix it, so the loop now stops when a failure is not tied to a scene).
6. **Every page showed the same picture** in the first story videos: all pictures are named `image.jpg` and overwrote each other. Found only by looking at frames.
7. **The image model painted words into a picture** despite "no text in the image" (HR-006).
8. **The quiz never reached the child** in the first full browser run: it is verified after the story, and the child reached the last page first. The end screen now offers the quiz when it is ready.
9. **Keys pasted into the chat** twice; both ended up in session transcripts and in Entire checkpoints. Rotate both before publishing.
10. **Entire Trails and review cannot run** until the GitHub App is connected on entire.io (web step).

## 5b. What each part of the repository is
| Path | What it holds |
| --- | --- |
| `src/storybound/` | the product: `pipeline.py` (graph), `agents/` (writer, planner, quizmaker, ...), `oath/` (catalogue, deterministic checks, engine, judge), `video/` (the video agent), `api.py`, `clients/` (Gemini, K2, images, TTS) |
| `web/` | the React app and its browser checks (`scripts/e2e-real.mjs`, `e2e-quiz-mock.mjs`) |
| `scripts/` | run and evidence tools: `sweep.py`, `report.py`, `run_story.py`, `story_video.py`, `make_video.py`, `quiz_story.py`, `build_evidence.py`, `lint_evidence.py`, `neatlogs_mcp.py` |
| `evidence/` | ledger, reports, hardening records, exported traces, screenshots, story packages, Entire and cfo.ai outputs |
| `docs/` | design, API, web, platforms, this process, the tool usage, the status; `planning/` holds the pre-kickoff plans |
| `video/harness/` | HyperFrames project template, vendored GSAP, claim catalogues |

## 6. Where to read next
[TOOLS.md](TOOLS.md) (how neatlogs, Entire and cfo.ai were used), [STATUS.md](STATUS.md) (what is left), [DESIGN.md](DESIGN.md), [API.md](API.md), [WEB.md](WEB.md), `hackathon.md`, `EVIDENCE.md`.
