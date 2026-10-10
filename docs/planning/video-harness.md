# Video harness and the three tracks: plan

Written 10 Oct 2026, ~14:45 IST. Deadline: submit Mon 12 Oct 19:00-23:55 IST. Read with `pitch.md` (the 3-minute script), `neatlog.md`, `entire.md`, `cfo.md`.

## 1. The idea in one paragraph

Storybound's thesis is "write the promises first, check every page against them, repair, ship a receipt". The launch video was made from a deterministic page (`video/launch/video.html`, scenes seeked frame by frame, piped to ffmpeg). Turn that into a **harness**: a *video agent* that takes a spec, renders it deterministically, **checks the result against a video oath, repairs what breaks, and ships a receipt**. Same pattern as the story agent, applied to a second artifact. Then the demo video, which is 20% of the score and must show every claim with evidence, is produced by the harness from the evidence files, so **no number on screen can be typed by hand**.

It is also a product feature: the same engine renders a child's finished story as a read-along video (pictures, narration, captions, receipt end card) at CPU cost only. That gives cfo.ai a real add-on line to price.

## 1b. Research (10 Oct 2026): what exists, what it teaches, what it changes

Read from primary pages where I could; claims marked "unverified" come only from a vendor or a blog. Nothing here was run yet.

### Open-source video harnesses and renderers

| Project | What it is | Licence | Fit |
| --- | --- | --- | --- |
| [HyperFrames](https://github.com/heygen-com/hyperframes) (HeyGen) | "Write HTML. Render video. Built for agents." HTML + CSS + seekable animations (GSAP, CSS, Lottie, Three.js, WAAPI), headless Chrome frame capture, FFmpeg encode, audio mixing with VO ducking. CLI `init/preview/lint/inspect/check/snapshot/render`; 21 agent skills (Claude Code plugin). Node 22+ and FFmpeg. About 60k stars on the repo page | Apache-2.0, no per-render fees | **Same model as our `video/launch`** (seek the page, screenshot each frame, pipe to ffmpeg). Best candidate to adopt as the render layer. What `lint`/`inspect` check is not stated on the README; determinism "same input, same frames" is the project's own claim, unverified by us |
| [Remotion](https://www.remotion.dev/docs/license/faq) | React/TypeScript, incumbent; official agent skills | Source-available: free for up to 3 people (we are 1), automated pipelines and prompt-to-video products fall under "Automators" ($0.01 per render, $100/month minimum); building a service that generates Remotion code with AI is allowed | Works, but a React build step for little gain, and a licence clause that matters if Storybound sells the video feature |
| [Revideo](https://github.com/redotvideo/revideo) | TypeScript, headless `renderVideo()`, audio export, serverless; 4.1k stars | MIT | Good for imperative animation; no agent tooling; maintenance date not visible on the page |
| Motion Canvas | Generator-function animation editor (Revideo's origin) | MIT | Hand-authored animations, not an agent target |
| [OpenEdit](https://github.com/veedstudio/open-edit) (VEED) | A skill: agent transcribes (WhisperX), composes an HTML page, renders frame by frame in a browser, **reviews the frames**, re-renders only what changed; no GUI | Apache-2.0 | Closest in spirit. Its verification is "the agent looks at frames"; the README says "expect rough edges". 25 commits, young |
| [agent-video-studio](https://github.com/mikolajmikolajczak0108/agent-video-studio) | JSON **reviewable edit plans**, FFmpeg/Whisper scripts, **export QC** (duration, frame timing, audio, colour, decoding); "the agent plans and reviews; the scripts execute explicit operations" | MIT | Right division of labour and the right kind of deterministic QC; but 0 stars and 3 commits, so a pattern to copy, not a dependency |
| edit-ai, WeftCut, OpenChatCut | Agents driving a timeline editor through MCP tools (16 and more tools; approval before destructive actions); OpenChatCut is AGPL | MIT / AGPL | A GUI timeline is the wrong target: we want deterministic code from a spec |

Result of the survey: **the renderer problem is solved and open**; I found no open-source harness (from the pages I read) that checks every number on screen against a source of truth, runs per-promise verification with repair, and ships a receipt. HyperFrames' `lint`/`inspect` and agent-video-studio's QC cover technical correctness only. That gap is our contribution and it is the same idea as the oath.

### What the agent-loop literature and engineering posts say (and where we already agree)

| Source | Finding | What we do with it |
| --- | --- | --- |
| Anthropic, [Harness design for long-running application development](https://anthropic.com/engineering/harness-design-long-running-apps) | Planner / generator / **separate evaluator** that drives the live output (Playwright) and files bugs against a shared definition of done (a "sprint contract"); out of the box the evaluator "talked itself into approving flawed work" and had to be calibrated with few-shot examples; the full harness cost about 20x the solo run ($200 vs $9) but produced working output the solo run did not; every harness component encodes an assumption about what the model cannot do alone, so re-test it when the model changes | Our judge is already a separate model (K2) from the writer (Gemini). The video oath is the contract, written before rendering. Keep the evaluator, drop anything that cannot show it changes the outcome; log cost of the loop honestly (B1 vs B0 does this for stories) |
| Anthropic, [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) | JSON feature list the agent may only flip `passes` on (JSON because models alter it less than Markdown); progress file + git commits so a fresh session recovers state; end each session clean; agents "declared victory early" and marked features done without end-to-end tests until told to test as a human would | The spec and the oath are JSON; promises have a status the repair loop may change but never delete. `hackathon.md` and the ledger are our progress file. Verify through the rendered output (frames, audio), not the spec |
| Anthropic, [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) | Workflows (predefined code paths) vs agents (LLM directs its own steps); **evaluator-optimizer** fits when criteria are clear; agents need ground truth from the environment at each step and a maximum iteration count; invest in tool design and make tools hard to misuse; start simple, no framework you cannot debug | Our video pipeline is a **workflow with one agentic loop** (verify then repair, max 2 attempts), not a free-roaming agent: video promises are clear and checkable. Tools validate at the boundary (a `claim` block cannot hold a literal number) |
| Huang et al., [LLMs Cannot Self-Correct Reasoning Yet](https://arxiv.org/abs/2310.01798) (ICLR 2024) | Without external feedback, self-correction often does not help and can hurt | Matches our own measurement so far: B2 (same model reviews its own story) ships a broken promise in about 90% of stories, B1 (external judge + deterministic checks) in 0 of 12 at the interim. Put B2 vs B1 in the video story, with the numbers from the final sweep |
| [Agentic Video Generation: text to executable event graphs via tool-constrained LLM planning](https://arxiv.org/abs/2604.10383) | A staged flagship-model pipeline produced 0 executable specs in 50 attempts; agents acting only through tools that check operations against simulator state produced valid specs 20 of 25 (80%) on a budget model; evaluated by round-trip reconstruction | Strongest support for "validate at the tool boundary". We borrow the idea (claim blocks resolve against evidence at write time) but not the simulator |
| [VideoAgent](https://arxiv.org/abs/2410.10076) (NeurIPS 2025) and VISTA (arXiv 2510.15831) | VLM as the reward/critic that selects or refines generated video plans | Supports the judged frame checks (legible, matches narration); these papers are about generative video, not deterministic render, so the evidence is indirect |

### What this changes in the plan

1. **Do not write a renderer from scratch.** Time-boxed spike (45 minutes, Sat evening): render two scenes of `scenes.json` with HyperFrames on this Windows machine (Node 24, ffmpeg present), compare frame-exactness across two runs (hash the frames), and read what `lint`/`inspect` catch. If it works, adopt it for render, audio mix and layout lint, and keep only our layers on top (spec, claim resolution, oath checks, repair, receipt, tracing). If it does not, keep `video/launch/render.mjs` (already works, ~100 lines) and add what is missing. Decision recorded in `hackathon.md` with the evidence either way.
2. **Our part is the verifier.** The differentiated work is `claims_sourced`, `claims_match_ledger`, `tools_covered`, `no_child_data`, `no_secrets` and the receipt: none of the projects above ship these.
3. **Keep the loop small** (Anthropic's own advice): workflow with one verify-repair loop, max 2 attempts, JSON spec/oath the repair step cannot delete from, external evaluator for judged checks. Measure the loop's cost against a no-verify run (B0-style arm for video) so the harness is itself an experiment with numbers.
4. **Licence**: HyperFrames Apache-2.0 and Revideo MIT are safe if the video export ships as a product feature; Remotion's Automators clause is a cost line for cfo.ai if we used it. Another reason to prefer HyperFrames.
5. **Honest caveats to carry into the submission**: HyperFrames' determinism and agent-friendliness claims come from its authors and blogs; the Anthropic cost figures are one project's; the self-correction paper is about reasoning, not video.

## 2. What exists and what is wrong with it

| Today (`video/launch/`) | Problem for a harness |
| --- | --- |
| `scenes.json` has only `id`, `text`, `min`, `hold`; all visuals live in 18 KB of hand-written JS in `video.html` | Not data-driven; an agent cannot edit a scene without editing code |
| `render.mjs` and `mix.mjs` hard-code `D:/storybound/...`, `C:/ffmpeg`, Edge path; `mix.mjs` duplicates the mix code | Not portable, two copies of one thing |
| Numbers and claims typed in the JS/text | Nothing checks them against evidence |
| No checks at all (length, overflow, loudness, secrets, faces) | Cannot verify, cannot repair |
| No trace, no receipt | Invisible to neatlogs and the judges |

What is good and stays: Web Animations seeked by `window.seek(t)` (frame-exact, repeatable), VO-length-driven scene timing, SFX cues registered by the page, ffmpeg mix with limiter.

## 3. Design (smallest thing that works)

```text
claims (evidence/*.json, ledger)  ──┐
                                    ▼
brief ──► PLAN (LLM) ──► spec.json ──► RENDER (node, deterministic) ──► out.mp4
          (scenes, claims refs,        TTS per scene (Gemini TTS)        │
           5-point tool coverage)      timeline = VO length + hold       ▼
                                                                    VERIFY (video oath)
                                           repair patch to spec ◄──  fail │ pass
                                           (only that failure)            ▼
                                                                   receipt.json + ledger row
```

- **Spec** (`video/harness/specs/*.json`): scenes of typed blocks (`title`, `drawing`, `claim`, `table`, `trace`, `receipt`, `caption`), each with narration text. A `claim` block holds `{label, source: "evidence/reports/…md#shipped_with_violation.B1"}`, never a literal number. The renderer resolves the value at render time. ~8 block templates replace the hand-written JS; scene-specific one-offs stay allowed as a `custom` block so we do not over-build.
- **Renderer** is a tool the agent calls: `render(spec) -> mp4 + timeline.json + frames sample`. Paths and binaries come from `.env`/`config`, not literals. One audio-mix function (delete `mix.mjs`).
- **Orchestration** in Python (LangGraph, like the story agent; neatlogs SDK is Python): nodes `plan -> tts -> render -> verify -> repair`, state carries the spec, verdicts and attempt count. No new framework.
- **Why a harness and not a script**: the agent chooses tools (resolve claims, TTS, render, probe, vision-check), keeps state across attempts, recovers from failures, verifies, and iterates, which are the eight capabilities neatlogs should show, on an artifact the judges can watch.

### The video oath (verified before the video is "shipped")

Deterministic (no model, cheap, run every time):

| Promise | Check |
| --- | --- |
| `length_ok` | duration <= 180 s |
| `claims_sourced` | every number/percent on screen comes from a `claim` block that resolves to an evidence file; no literal digits in narration or captions outside claims (regex on spec) |
| `claims_match_ledger` | resolved values re-computed from `evidence/ledger.jsonl` equal what `report.py` printed |
| `tools_covered` | for neatlogs, Entire, cfo.ai: scenes labelled architecture, implementation, runtime, reasoning, result (all 15 present) |
| `no_overflow` | in the page, no text box scrollWidth/Height > client size at any scene midpoint |
| `audio_ok` | every scene has VO; loudness within -16 +/- 2 LUFS (ffmpeg `ebur128`); no clipping |
| `no_secrets` | spec, narration, claim values and the page text match none of the secret patterns used by `lint_evidence.py`; no URL with a token |
| `no_child_data` | no image outside `assets/` and `fixtures/` allow-list; no file under `_private/` |

Judged (vision model on ~12 sampled frames, one call per frame batch):

| Promise | Check |
| --- | --- |
| `legible` | text readable at 1080p, no clipped or overlapping elements |
| `matches_narration` | what is on screen supports the sentence being spoken |
| `no_face` | no child's face visible |

Repair loop = the story agent's loop: a failing promise goes back to the planner with only that failure and the offending scene; max 2 attempts per promise; unresolved failures are listed in the receipt, never hidden.

**Receipt** (`evidence/video/<name>/receipt.json`): spec hash, claim table (label, value, source file, source hash), per-promise verdicts, repairs, tokens, cost, seconds, git sha, neatlogs trace id. The demo ends on this receipt, the same object the child's parents get for a story.

## 4. Integrating the three tracks

### neatlogs (25% with the other two; flight recorder)

- Every harness run is **one trace** (`WORKFLOW` root, node spans, tool spans for TTS/render/probe, one `GUARDRAIL` span per video promise with `neatlogs.guardrail.passed`). Reuse `storybound/tracing.py`; the only module importing neatlogs stays the observer.
- **Rule you set, made a gate**: after every named run, verify the trace appears in the dashboard before moving on (script: look the trace id up via MCP `search_traces`; fail loudly if missing; store the readback in `evidence/traces/`). Add the check to `sweep.py`/`run_story.py` and the harness so it cannot be forgotten.
- Investigate failures from traces first, as `CLAUDE.md` requires: hypothesis in `hackathon.md`, fix, second run, compare trace ids. Two hardening records already queued (HR-001 reading level, HR-002 latency); the harness adds **HR-003** from the first real harness failure (expected: text overflow or a claim that does not resolve). We do not stage failures.
- Detections: add "Video promise failed" next to "Oath violation" (free plan has 5 slots, 3 are defaults, so 2 left: this is the last one; do not spend it elsewhere).
- **Blocker found this session**: the neatlogs MCP in `.mcp.json` returns 401 "Invalid API key" at startup (`AUTH_HEADER_REJECTED`). Until the key in the environment is fixed, verification goes through `scripts/neatlogs_mcp.py` (HANDOFF says this path works). Needs your action if the key was rotated.

### Entire (checkpoints, Trails, Graph, Brain)

- **0 checkpoints today** because earlier work ran outside the repo. From now on this session and every later one runs inside `D:\storybound`; one commit per intent so each checkpoint maps to one change; start a fresh Claude session per task. After each key commit record (sha, `Entire-Checkpoint` id, trace id) in the hardening record immediately.
- Harness work is committed in this order (each is a checkpoint): (1) extract renderer + portable config, (2) spec + claim blocks, (3) verify promises, (4) agent loop + tracing, (5) HR-003 fix, (6) final demo spec.
- **Trails**: submit the access form from `hack.entire.io/neathacks-2026/`, ask a repo admin (you) to enable Runners, Auto build and Trails on entire.io, then run the harness work as a trail: one branch, one PR from intent ("video agent that verifies its own claims") to shipped code. `entire review` and `entire dispatch --local` work without Trails, so use them either way and keep the output in `evidence/entire/`.
- **Graph**: `graph impact` on `verify`/`render` before editing, `graph diff` and `graph verify` after, outputs in `evidence/entire/` (same as for `verify_scene_async`).
- **Brain**: `entire brain brief` at the start of each task; `entire brain remember` for durable facts (e.g. "claims in video specs must be source refs, never literals").
- **Submission link and ID**: `https://entire.io/gh/hatif03/storybound/commit/<FULL_SHA>` plus the 26-char checkpoint id from the trailer. The repo is **private**; the link is only "accessible" to judges if the repo is public or they are granted access, so publish before Monday 19:00 (decision for you, with the privacy checks in `entire.md`: checkpoints live in the repo and become public with it).
- `entire login` is done. Remaining: `entire status` after the next commit to confirm the first checkpoint appears.

### cfo.ai (business plan, measured cost input)

- Use the cfo.ai MCP (authorise it in the VS Code MCP prompt if tools ask) to build the plan from `docs/planning/cfo.md`: Plan dimension (Household, Classroom) and **add-on dimension (Story video)**, Main and Growth scenarios; revenue, infra, inference, gross profit, gross margin, runway.
- Inputs that must be **measured, not assumed**: cost per story from neatlogs (B0 about $0.0086, B1 about $0.0176 estimated from sweep 2 so far; replace by neatlogs cost on the final sweep and label the estimate until then) and **cost per rendered video** from harness receipts (TTS + render seconds; the story's images are already paid).
- Pricing decision the model must make and justify: price per plan, per-story overage, whether verification is on for every page or sampled (the B1 vs B0 cost gap is the lever), video add-on price. Bar from `cfo.md`: gross margin >= 60% on Main, stretch 70%.
- Revenue and market inputs: Crustdata (key in `.env`) for the number of children's-content and ed-tech buyers; derived figures only, cited "Crustdata, 12 Oct" (date of the pull); no raw data in the repo; nothing about children sent to it.
- **Deliverable for the submission**: the shared cfo.ai page URL, the Version-history screenshot of the cost input replaced by the neatlogs measurement, and an export of the plan (tables as CSV/markdown) in `evidence/cfo/`, so the repo does not depend on the dashboard. Add a short `evidence/cfo/BUSINESS-PLAN.md` (pricing, cost, revenue, runway, the decision made and why).

## 5. Advancing the agents (the "agents" score is 30%)

Story agent, from the data we already have:

1. Finish sweep 2, write HR-001/HR-002. Interim: B2 (self-critique) ships a broken promise in about 90% of stories, so it does not close the gap; B1 still fails `age_reading_level` on the first pass more than B0 (9/12 vs 1/12), which needs a trace-backed explanation before we claim p2 fixed it.
2. Hardening candidate: text-only fixture flips between sanitise and ask-redraw. Make a regression fixture.
3. "Forget this story" delete endpoint (privacy claim for parents).
4. Parent/teacher-written promises (free text becomes a judged `lesson_specific_*` commitment): small, the strongest differentiator, and it makes the cfo.ai Classroom plan concrete.

Coding agent (Entire): see section 4; the evidence is the checkpoint-per-intent discipline.

Video agent: section 3.

## 6. Schedule (IST)

| When | Work | Evidence produced |
| --- | --- | --- |
| Sat 10 Oct, now to ~18:00 | Sweep 2 finishes; HR-001/002; report; commit with checkpoints. HyperFrames spike (45 min, see 1b), then renderer decision + spec + claim blocks (commits 1-2). Trace-readback gate. | `reports/`, `hardening/`, first Entire checkpoint ids |
| Sat evening | cfo.ai model first pass from sweep-2 costs. Entire Trails access form. | `evidence/cfo/` draft |
| Sun 11 Oct, morning | Video oath checks + verify node (commit 3); run it on the existing launch video as the first baseline (expect failures: literals, no receipt) | trace of the baseline run, ledger row |
| Sun midday | Agent loop with repair, tracing (commit 4); first real failure becomes HR-003 (commit 5) | before/after traces, checkpoint ids |
| Sun afternoon | Story export through the same harness (read-along video of one real story, media on); web UI real-story run fixes | receipt, screenshot |
| Sun evening | cfo.ai final: measured inputs, Version history screenshot, plan export; Crustdata derived figures | `BUSINESS-PLAN.md` |
| Mon 12 Oct, morning | Freeze code. Generate the <= 3:00 demo from the final ledger with the harness; the receipt proves each number | `evidence/video/demo/receipt.json` |
| Mon afternoon | `build_evidence.py`, `lint_evidence.py`, publish repo, record Entire link+ID, post log | `EVIDENCE.md` |
| Mon 19:00-23:55 | Quote-post the submission. Submit by 20:00 if possible; buffer to 23:55 | `posts.md` |

## 7. Not doing (and why)

- A general-purpose video editor, timeline UI, or a generative video model: the point is a deterministic renderer with a checker; generative clips are slow, costly, and cannot be verified.
- Many block templates: start with 8, add one only when a scene needs it.
- Anything that sends a child's drawing, face or voice to a new service.

## 8. Risks

- **Scope**: harness work must not starve the story agent and the three evidence tracks. Cut order if late: judged frame checks, story-export video, custom blocks. Keep: claim-sourcing, length, receipt, trace.
- **Children's images in the video**: `video/launch/img/cutout-sister*.png` and the `draw-*.jpg` drawings are a real child's work. CLAUDE.md rule 3 allows them only with a parent's consent, no surname, school or place, and no face. Confirm before publishing; the `no_child_data` allow-list should default to fixtures only.
- **Dashboard expiry**: free-plan traces expire; keep exports in `evidence/traces/`.
- **Machine-specific tooling**: Edge and ffmpeg paths; the extraction commit fixes this.
