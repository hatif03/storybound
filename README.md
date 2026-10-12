# Storybound

### A bedtime-story helper that checks its own work, so a parent doesn't have to.

A child draws a hero. Storybound turns the drawing into a short storybook that teaches a gentle lesson (sharing, honesty, kindness, patience), reads it aloud, and asks a kind question on every page. **Before any page reaches the child, the app has checked it against promises it wrote down first, rewritten what broke, and afterwards it hands the parent a plain receipt of what it kept.**

| Try it | Link |
| --- | --- |
| **Live app** (real stories, limited per day; please use the sample drawings or draw your own, not a real child's photo) | http://ec2-34-237-142-143.compute-1.amazonaws.com/ |
| **Free demo mode** (same screens, no models, no limit) | http://ec2-34-237-142-143.compute-1.amazonaws.com/?mock=1 |
| **3-minute video** (about 3:07: the app from drawing to receipt, then how neatlogs, Entire and cfo.ai helped) | http://ec2-34-237-142-143.compute-1.amazonaws.com/videos/storybound-demo-3min.mp4 |
| **Full tour video** (about 19 minutes: every screen, including the grown-up side, the movie and the receipt) | http://ec2-34-237-142-143.compute-1.amazonaws.com/videos/storybound-full-tour.mp4 |
| **Why a family would want it, and who it helps** | [docs/WHY.md](docs/WHY.md) |
| Videos on GitHub (backup copies of both) | https://github.com/hatif03/storybound/releases/tag/demo-videos |
| **For the judges: how we used neatlogs, Entire and cfo.ai** (answers, screenshots, evidence links) | http://ec2-34-237-142-143.compute-1.amazonaws.com/judges/ and [below](#how-we-used-the-tools-the-submission-forms-questions-answered) |

## The problem
AI can write a story about your child's own drawing in seconds. It is also a fast writer that does not know what is right for a five-year-old, and nobody is watching it. In our own experiment the same writer, left alone, slipped at least one broken promise into **27 of 28** stories: a lesson that never showed up, the right answer always in the same place, words too hard for the age, sometimes an unkind line. A parent cannot read every story first, and a child on a tablet is often alone with it. So today a parent can only refuse these tools or trust them blindly.

## The solution: use them, and check them
1. **Draw and choose.** A child draws a hero (or a grown-up photographs a drawing) and picks a lesson. A grown-up may add a promise of their own, such as "nobody in the story is left out".
2. **Promises first.** The agent writes an *oath* for this drawing and lesson before any story exists: age-appropriate words, the hero on every page, the lesson really taught, nothing scary or unkind, no stray words painted into pictures.
3. **Checked before it is shown.** Each page is checked against the oath by simple rules and by a second, independent AI from a different family. A page that breaks a promise is rewritten. A page is shown only when its words, picture and voice all exist, and then it reads itself aloud (with a "Listen again" button). Every page ends with a gentle choice; a wrong answer is never a scolding. Then a short quiz, a picture game, and an optional read-along movie.
4. **A receipt for the grown-up.** Behind a grown-up gate: how many promises were checked, which pages were rewritten, and anything that could not be fully kept. Nothing is hidden, and a parent can make the app forget the story.

**The result:** with every page checked, **0 of 28** stories shipped with a broken promise, against **27 of 28** without ([report](evidence/reports/20261010-1505-IST-sweep-2-p2.md)). It costs about two cents of text per story, around twenty cents with pictures and a voice (estimates in [docs/BUSINESS.md](docs/BUSINESS.md)), cheap enough for schools and libraries. Who it helps and why it matters: [docs/WHY.md](docs/WHY.md).

## How we used the tools (the submission form's questions, answered)
Full page with screenshots, tables and every link: **http://ec2-34-237-142-143.compute-1.amazonaws.com/judges/** (also in the repo at `web/public/judges/index.html`). Dashboard screenshots: [evidence/dashboards/](evidence/dashboards/). The same answers are in [docs/SUBMISSION.md](docs/SUBMISSION.md) for copy and paste.

### neatlogs: what did you trace, debug or improve?
We traced every story as **one trace**: the oath, each page, each judge call, each picture and voice, with every promise check as its own span holding the quoted words and the verdict. We then used neatlogs to find our own bugs, always trace first, then fix, then compare runs:
- **Reading level** broke on most first-pass pages; telling the writer the limit cut pages over the limit from 42.9% to 1.8% ([HR-001](https://github.com/hatif03/storybound/blob/main/evidence/hardening/HR-001.md), [HR-003](https://github.com/hatif03/storybound/blob/main/evidence/hardening/HR-003.md)).
- **neatlogs's own triage cards** (an 87 s Gemini stall, "hurts" flagged critical, a PII card): one confirmed, one partly, one refuted, each checked before any fix ([TRIAGE-REVIEW](https://github.com/hatif03/storybound/blob/main/evidence/neatlogs/TRIAGE-REVIEW.md), [HR-004](https://github.com/hatif03/storybound/blob/main/evidence/hardening/HR-004.md), [HR-011](https://github.com/hatif03/storybound/blob/main/evidence/hardening/HR-011.md)).
- **Error spans** of a stronger writer showed 3 of 10 stories ending in a page-format error; after a tolerant parser, 10 of 10. **Drills** we ran on purpose showed no story shipping with the judge down (0 of 5); with a judge from another family, 5 of 5 ([HR-014](https://github.com/hatif03/storybound/blob/main/evidence/hardening/HR-014.md), [HR-015](https://github.com/hatif03/storybound/blob/main/evidence/hardening/HR-015.md)).
- **Incident cards** ("repair loop never ends", "latency in illustrate", "K2 returns prose") were checked against their traces: the repair cap holds, one was our own drill, one was refuted by the span, and the first exposed a fault of ours (pictures and judge calls missing from the story's trace: 2 of 4 pictures before, 4 of 4 after). Fixed, with the before and after traces saved ([HR-016](https://github.com/hatif03/storybound/blob/main/evidence/hardening/HR-016.md)).
- **Detections, alerts and evaluations:** a picture-words detection that was blind until the fix then fired on a drill; seven alert rules with email delivery; a human evaluation of single judge verdicts ([neatlogs evidence](https://github.com/hatif03/storybound/blob/main/evidence/neatlogs/), [screenshots](evidence/dashboards/neatlogs/)).
- **Measured cost** ($0.0199 per story, about 20% above our estimate) replaced the estimate in the cfo.ai model.

### Entire: how did you use it?
Entire recorded the coding agent that built Storybound (97 checkpoints in 132 commits, 4 trails merged, per its analytics).
- **Checkpoints, progress and key decisions:** one commit per intent so each checkpoint maps to one change; every hardening record names its commit and checkpoint ([evidence/hardening](https://github.com/hatif03/storybound/blob/main/evidence/hardening/)); the submission checkpoint is [commit 1a96c19](https://entire.io/gh/hatif03/storybound/commit/1a96c19fd6f99c981f7e6b7cbbea715d25eb55d2) (checkpoint `01M4MJM5TRM7NE2F8FHFJ49NE6`). Decisions kept include the safety-word tiering ([HR-004](https://github.com/hatif03/storybound/blob/main/evidence/hardening/HR-004.md)), pipelined review with the honest result that time to first page did not improve ([HR-002](https://github.com/hatif03/storybound/blob/main/evidence/hardening/HR-002.md)), and the history rewrite after keys reached checkpoint refs ([note](https://github.com/hatif03/storybound/blob/main/evidence/history-rewrite/NOTE.md)).
- **entire-graph, finding code and assessing risky changes:** `graph impact` before touching the safety words ([story_safe_text](https://github.com/hatif03/storybound/blob/main/evidence/entire/20261010-1421-IST-graph-impact-story_safe_text.txt), [verify_scene_async](https://github.com/hatif03/storybound/blob/main/evidence/entire/20261010-1421-IST-graph-impact-verify_scene_async.txt)), seven `graph diff` runs after changes ([HR-001](https://github.com/hatif03/storybound/blob/main/evidence/entire/20261010-1716-IST-graph-diff-HR-001-04ffebb.json), [HR-004](https://github.com/hatif03/storybound/blob/main/evidence/entire/20261010-1953-IST-graph-diff-HR-004-748ce42.json), [the picture agent](https://github.com/hatif03/storybound/blob/main/evidence/entire/20261011-1300-IST-graph-diff-auto-pictures-touch-early-painting.json)), and `entire why` on the oath catalog and prompts ([catalog](https://github.com/hatif03/storybound/blob/main/evidence/entire/20261010-1953-IST-why-catalog.txt)).
- **Reviews and trails that improved the project:** `entire review general` found 5 issues on PR 1 (one a real evidence-builder bug), 8 on PR 2 (a missing fallback that would have turned a gateway outage into failed stories) and 7 real defects in our own failure fixes on PR 4 ([PR 1](https://github.com/hatif03/storybound/blob/main/evidence/entire/20261011-1010-IST-review-general-pr1.txt), [PR 2](https://github.com/hatif03/storybound/blob/main/evidence/entire/20261011-1415-IST-review-general-pr2.txt), [PR 4](https://github.com/hatif03/storybound/blob/main/evidence/entire/20261012-IST-review-general-pr4.txt)). The trail runners flagged a chaos-injection setting that could reach production (fixed, commit `c692d89`) and an autoplay rule conflict (resolved by writing the rule precisely, [WEB.md](https://github.com/hatif03/storybound/blob/main/docs/WEB.md)). Trails: [2](https://entire.io/gh/hatif03/storybound/trails/2), [4](https://entire.io/gh/hatif03/storybound/trails/4), [5](https://entire.io/gh/hatif03/storybound/trails/5).
- **Open-source builds on Entire's CLI, Graph or External Agents:** we did not contribute code to Entire's own repositories. We built on top of them: six Trail runners tailored to this project's hard rules in [.entire/runners](https://github.com/hatif03/storybound/tree/main/.entire/runners), custom key redactions after a key reached a checkpoint, Claude Code with commit linking `always`, and evidence scripts ([build_evidence.py](https://github.com/hatif03/storybound/blob/main/scripts/build_evidence.py), [lint_evidence.py](https://github.com/hatif03/storybound/blob/main/scripts/lint_evidence.py)) that read checkpoints and traces. Gaps we hit are documented in [TOOLS.md](https://github.com/hatif03/storybound/blob/main/docs/TOOLS.md).

### cfo.ai: how did it shape your business plan?
cfo.ai turned "what does a story cost?" into product decisions ([public model](https://app.cfo.ai/s/vGE_ZEwfQtpoxPrg), [BUSINESS.md](https://github.com/hatif03/storybound/blob/main/docs/BUSINESS.md)):
- **Pictures:** painting every page leaves a 43.4% month-6 margin against our 60% bar; half the pages clears it at 67.8%. So the agent now spends a fixed picture budget on the pages that matter most ([HR-010](https://github.com/hatif03/storybound/blob/main/evidence/hardening/HR-010.md)).
- **Measured cost:** the cost input is the number neatlogs measured, not a guess; Version history shows the edit ([screenshot](evidence/cfo/20261012-1332-IST-cfo-version-history-unit-economics.png)).
- **Video AI:** four scenarios showed three of the cheapest clips taking the margin from 67% to minus 70%, so video is left out and motion stays deterministic and checked.
- **A real launch:** a launch plan with operating and one-time costs (labelled as assumptions): about 2,490 paying households at $6.99 to break even. Workbooks: [evidence/cfo](https://github.com/hatif03/storybound/blob/main/evidence/cfo/), [screenshots](evidence/dashboards/cfo.ai/).

## What it looks like
The web app, desktop width. Screens marked *live* came from a real story run through the browser (`web/scripts/e2e-real.mjs`, real models); screens marked *demo mode* come from the free scripted mode (`?mock=1`), which shows the same screens without calling any model. The drawings are test fixtures or drawn by the test script, never a real child's.

| | |
| --- | --- |
| ![Draw your hero](docs/img/01-draw.png)<br>**1. Draw a hero** (live) | ![Pick a lesson and add a grown-up promise](docs/img/02-lesson-grownup-promise.png)<br>**2. Pick a lesson; a grown-up may add promises** (live) |
| ![Reading a page while its picture is painted](docs/img/03-reader-live.png)<br>**3. A verified page; the picture arrives after the words** (live) | ![A finished page with picture and feedback](docs/img/04-reader-picture-demo.png)<br>**4. A page with its picture and a kind-choice reply** (demo mode) |
| ![A quiz question with the story line shown](docs/img/05-quiz-live.png)<br>**5. Quiz: every answer points to a line in the story** (live) | ![The end screen with games and the promises kept](docs/img/06-end-games-demo.png)<br>**6. The end: promises kept, quiz, order game, movie** (demo mode) |
| ![The grown-ups receipt](docs/img/07-receipt-demo.png)<br>**7. The receipt for grown-ups, promise by promise** (demo mode) | ![The read-along movie, title card](docs/img/08-movie-drawing.png)<br>**8. The movie made from the story: the drawing becomes the hero** (real render) |
| ![The read-along movie, a story page with its choice](docs/img/09-movie-page.png)<br>**9. A movie page with the kind choice** (real render) | |

## Read this first (for judges)
| If you want | Open |
| --- | --- |
| Why a family would want it, and who it helps | [docs/WHY.md](docs/WHY.md) |
| Dashboard screenshots and the recordings' timestamps | [evidence/dashboards/](evidence/dashboards/) |
| The live deployment (how it was set up, limits, how to shut it down) | [docs/DEPLOY.md](docs/DEPLOY.md) |
| Submission checklist | [docs/SUBMISSION.md](docs/SUBMISSION.md) |
| How the demo videos were made | [docs/DEMO-RECORDING-GUIDE.md](docs/DEMO-RECORDING-GUIDE.md), [docs/DEMO-SCRIPT.md](docs/DEMO-SCRIPT.md) |
| How it was built, hour by hour, and what went wrong | [docs/PROCESS.md](docs/PROCESS.md) |
| How neatlogs, Entire and cfo.ai were used (architecture, implementation, runtime, reasoning, result) | [docs/TOOLS.md](docs/TOOLS.md) |
| What is done and what is left | [docs/STATUS.md](docs/STATUS.md) |
| Why it fits the hackathon's problem statement | [docs/QUALIFICATION.md](docs/QUALIFICATION.md) |
| If this launched to real children: situations, what is built, what is open | [docs/LAUNCH-READINESS.md](docs/LAUNCH-READINESS.md) |
| How neatlogs, Entire and cfo.ai helped, as a story with evidence | [docs/STORY.md](docs/STORY.md) |
| What a real product needs, and what video AI would cost (cfo.ai scenarios) | [docs/BUSINESS.md](docs/BUSINESS.md) |
| The hackathon credits and how work is split across providers | [docs/CREDITS.md](docs/CREDITS.md) |
| A second pass through every neatlogs trace, detection, alert and analytics view | [docs/research/neatlogs-incident-review.md](docs/research/neatlogs-incident-review.md) |
| Research: evaluation practice (SWE-bench, OpenAI) and video generation (Veo access, landscape, plan) | [docs/research/evals-and-observability.md](docs/research/evals-and-observability.md), [docs/research/video-generation.md](docs/research/video-generation.md) |
| Every claim with its evidence | [EVIDENCE.md](EVIDENCE.md) (generated) and `evidence/` |
| The agent's design | [docs/DESIGN.md](docs/DESIGN.md) |
| The HTTP contract | [docs/API.md](docs/API.md) |
| The web app, healthy-play rules | [docs/WEB.md](docs/WEB.md) |
| The build log, dated | [hackathon.md](hackathon.md) |
| State of every platform | [docs/PLATFORMS.md](docs/PLATFORMS.md) |

## The pieces
- **Story agent** (`src/storybound/`): safety screen, character card, oath, planner (scores each beat's importance), page loop with pipelined review and repair (LangGraph), whole-story gate, quiz, pictures (the agent chooses which pages to paint within a budget), narration, receipt. Arms: **B0** ungated, **B1** gated (the product), **B2** the same model reviews its own story.
- **Oath** (`src/storybound/oath/`): 22 core promises plus lesson-specific ones, grown-up promises and 6 quiz promises, checked by deterministic code and an independent judge (K2, a different model family from the writer) with a verbatim-quote check.
- **Video agent** (`src/storybound/video/`): plans or reads a spec of typed blocks, resolves every number from an evidence file, narrates, builds and renders with HyperFrames, checks its own **video oath**, repairs the failing scene, and ships a receipt. Used for the read-along video of a story and for the demo video.
- **Web app** (`web/`): draw, pick a lesson, read, quiz and game, movie, grown-ups area (receipt, settings, forget). Built for small hands: hold-to-confirm for anything that throws work away, palm and ghost-tap guards, a drawing that survives a reload and a "start over" that can be undone ([docs/WEB.md](docs/WEB.md#small-hands-touch-safety)).
- **Evidence** (`evidence/`): the run ledger, sweep reports, seven hardening records, exported neatlogs traces, screenshots, Entire and cfo.ai outputs.

## Numbers you can check
| What | Value | Where |
| --- | --- | --- |
| Stories shipped with a broken promise (B0 / B2 / B1) | 27/28, 27/28, **0/28** | `evidence/reports/*sweep-2-p2.md` |
| Hardening records, each with before and after | HR-001 to HR-016 | `evidence/hardening/` |
| Judge on 24 injected faults | 24/24 caught, 0/8 clean pages flagged | `evidence/runs/20261010-1334-IST-judge-eval.json` |
| Text cost per gated story, measured by neatlogs | $0.0199 | `evidence/neatlogs/20261010-2010-IST-measured-vs-estimated-cost.json` |
| Month-6 gross margin (cfo.ai, Main / Growth / Downside) | 67.2% / 55.2% / 40.9% (estimates) | https://app.cfo.ai/s/vGE_ZEwfQtpoxPrg |
| Tests | 107 backend, 29 web (plus 11 browser checks for touch safety) | `pytest tests`, `npm run test` in `web/` |

## Run it (development)
```powershell
uv sync                              # creates .venv from pyproject.toml
copy .env.example .env               # fill in the keys; never commit .env
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m uvicorn storybound.api:app --app-dir src --port 8000   # serves the API and web/dist
cd web; npm install; npm run build   # the web app, served at http://127.0.0.1:8000
```
Google credentials come from `gcloud auth application-default login`. Demo mode (no models, free): open `http://127.0.0.1:8000/?mock=1`.

Useful commands:
```powershell
.venv\Scripts\python.exe scripts\run_story.py benign/bunny-bow-carrot --lesson sharing --media --name my-run   # one story, one ledger row
.venv\Scripts\python.exe scripts\sweep.py --name my-sweep --arms B0,B1,B2 --fixtures ... --lessons sharing,honesty --k 2
.venv\Scripts\python.exe scripts\report.py --name my-sweep           # the sweep report
.venv\Scripts\python.exe scripts\story_video.py evidence\stories\bunny-sharing-2   # read-along video from a story package
.venv\Scripts\python.exe scripts\build_evidence.py; .venv\Scripts\python.exe scripts\lint_evidence.py
node web\scripts\e2e-real.mjs        # a real story through the real UI (costs about $0.40 plus $0.04)
```

## Rules this project keeps (`CLAUDE.md`)
All code written inside the hackathon window (first commit Sat 10 Oct 12:30 IST); secrets only in `.env`; no real child's data in the repo, traces, ledger or posts (fixtures only; real drawings stay in the gitignored `_private/`); no Google ADK; AWS limits respected; no raw Crustdata data in the repo.

## Privacy and healthy play, in short
No accounts, ads, tracking or purchases. No timers, lives, streaks or scores for the child and no autoplay chains (a page reads itself aloud, nothing else starts on its own); every game is skippable; practice results stay in the browser tab. A parent can **forget a story**: the server deletes its pictures, narration, drawing and video (`DELETE /api/stories/{id}`). neatlogs traces keep names and places redacted and expire on their own.

## For the judges: does it fit the problem statement?
*"Build an AI agent, or a team of agents, that completes a substantial task from start to finish. Give it a goal, tools and an environment; let each result guide its next action."* **Yes**, in four lines (full case with evidence and limits: [docs/QUALIFICATION.md](docs/QUALIFICATION.md)):
- **Goal, tools, environment:** a drawing and a lesson become an oath (a checkable list of promises); tools are vision, a writer, an independent judge from another model family, pictures, voice, deterministic checkers and a video renderer; the environment is a LangGraph run with state, quotas, budgets and a child using a real web app.
- **Each result guides the next action:** a failed check rewrites that page; a judge's quoted objection rolls the run back to that page; a quota error waits and retries, then degrades that page to text and says so; a quiz question that cannot be verified is dropped; a movie scene that fails its own checks is repaired. Gated, the same writer shipped a broken promise in **0 of 28** stories after fixing breaks on 19 first passes (1.82 repairs per story); ungated or self-reviewing, **27 of 28**.
- **Substantial, start to finish:** drawing, safety screen, character, oath, eight verified pages, whole-story check, verified quiz, pictures, narration, receipt, then a read-along movie, with no human step in between.
- **Said plainly:** it is a bounded agentic workflow (a fixed stage order with open-ended repair inside it, by design for children's content), not an open-ended tool-picking agent; the judge is not a human; samples are small.
