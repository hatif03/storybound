# Storybound: design

A children's (age 4-8) storybook agent. A child's drawing and a lesson go in. The agent writes an **oath** (what the story owes the child), writes the story page by page, **checks every page against the oath before the child can see it**, rewrites pages that break it, and ships a **receipt** a parent can read. If the drawing is unsafe it refuses calmly.

This document is the source of truth for the build. `docs/API.md` is the contract between backend and web. `docs/PLATFORMS.md` tracks the state of every tool we use.

## 1. The ideas

1. **The oath comes first.** Before any story text exists, the agent writes a list of promises for this drawing and lesson. A fixed core is always present; the model may add promises, never remove or relax one. The oath is hashed and recorded before the first page.
2. **Verification is inside the run.** Each page is checked as it is written. A broken promise triggers a bounded repair (two attempts), not an alert after the fact. A safety failure stops the run.
3. **The judge is independent.** Where a check needs judgement it runs on a different model family from the writer, must quote the text it relies on, and the quote is verified by code. Where a deterministic check exists it decides.
4. **Safety fails closed.** Missing or unparseable safety signals refuse; they never default to safe. Text inside the drawing is data, never instructions.
5. **Everything is evidence.** Every verdict is the same object: a span in neatlogs, a row in the ledger, a line on the receipt and a fixture for regression tests.

## 2. The task, end to end

Input: a drawing (PNG/JPEG or a fixture id), a lesson id, an age band (4-8), optionally a hero name.
Output: a character card, eight pages (scenario, question, two choices with one correct, feedback, image prompt), an illustration and narration per page, and a receipt. Or a refusal.

## 3. The oath

### 3.1 The verdict object (one shape everywhere)

```
commitment      stable id                         scope     run | story | scene i | image i | audio i
status          pass | warning | violation | critical | skipped | verification_error
verdict_by      deterministic | judge | both      det_status, judge_status (when run)
sampled         true | false, with seed and rate  judge_model (family and id) or none
expected        what the oath says                actual   what was found
evidence        page number and verbatim quote (judge) or matched token (deterministic)
cover           what this check claims to cover   attempt  0 first pass, 1..2 repairs
```

### 3.2 The commitment catalog (the fixed core is marked core)

| Commitment | Scope | Verifier | On failure |
| --- | --- | --- | --- |
| `input_safe_visual` (core) | run | independent vision screen plus blocklist; fail closed | critical: refuse |
| `no_drawing_text_obedience` (core) | run | deterministic: harmful tokens extracted from the drawing are absent from every page and prompt | repair once, then stop |
| `original_character_only` | run | judge on the character card (no recognisable existing franchise hero) | repair once, then neutral hero |
| `card_traits_checkable` | run | deterministic: at least three concrete visual traits | re-run vision once |
| `story_safe_text` (core) | scene | deterministic blocklist, judge sampled at 1.0 | critical: quarantine and regenerate once, then stop |
| `schema_valid` (core) | story | exactly 8 pages numbered 1-8, all fields present | repair |
| `one_correct_choice` (core) | scene | exactly one `is_correct` | repair |
| `correct_choice_position_balanced` | story | the correct slot is not the same in more than 5 of 8 pages | programmatic shuffle |
| `character_named_in_scene` | scene | the hero's name appears in scenario and question | repair |
| `visual_trait_referenced` | scene | a canonical trait appears in scenario or image prompt | repair |
| `age_reading_level` | scene | sentence and word-length bounds for ages 4-8, at most 2 sentences | repair |
| `lesson_concept_in_scene` | scene | deterministic lesson-term check, judge sampled | repair |
| `lesson_alignment` | story | judge with quote; pass at 0.7 | repair the weakest pages |
| `correct_choice_teaches_lesson` | scene | judge with quote | repair |
| `no_repeated_scenario` | story | deterministic similarity | repair the later page |
| `trait_in_image_prompt` | image | deterministic | repair prompt |
| `image_matches_card` | image | vision judge with the real image bytes, sampled; pass at 0.8 | regenerate once, then record |
| `illustration_present` | image | bytes returned, sane size | retry once, then degrade |
| `narration_present` | audio | non-empty audio, measured length within a band of the word-count estimate | retry once, then degrade |
| `lesson_specific_*` | scene or story | added by the oath author for this lesson | judge, repair |
| `contract_coverage` | run | computed, not judged | reported |

### 3.3 Mechanics

- **Order:** deterministic first; if it fails, stop there. If it passes, the judge runs when `rng(seed, commitment, attempt) < sampling_rate`. Both verdicts are kept; the stricter wins. Sampling is seeded and recorded. Safety commitments are always sampled at 1.0.
- **Judge contract:** temperature 0, structured output with `status`, `evidence.scene`, `evidence.quote`, `reasoning`. If the quote is not a substring of the text under review the verdict becomes `verification_error`.
- **Failure policy:** `verification_error` on a safety commitment fails closed; on a quality commitment it fails open and produces a flagged `warning`, so a story is never presented as checked when it was not.
- **Coverage:** every output field (scenario, question, options, feedback, image prompt, narration text) and every tool declares which commitments touch it. `contract_coverage_pct` and the uncovered names are reported. Uncovered behaviour is the first thing a hardening cycle looks at.
- **Thresholds:** one config file. Pass bars: lesson alignment 0.7, image match 0.8. Detection triggers: lesson < 0.6, image < 0.7, cost per story and latency set from measured numbers.

## 4. Architecture

```
drawing + lesson + age
        │
   intake  (hash input, run id, seed, budget, deadline, prompt versions)
        │
   safety_screen  TOOL   visual flag + text extracted from the drawing
        │ Tier A → refuse (traced)       Tier B → sanitise, continue      error → refuse
   vision_character  AGENT   character card (name, ≥3 checkable traits, palette)
        │
   oath_author  AGENT   core commitments + lesson-specific additions; hash the oath
   story_planner  AGENT   8 beats (runs at the same time as the oath author; gated arm only)
        │
   scene loop, i = 1..8, pipelined
     scene_writer(i)  AGENT   inputs: oath summary, card, beat i, rolling summary
     verify (cheap checks, now)   a failed cheap check → repair_scene(i) at once, judge after the repair
     submit → the slow judge reviews page i in the background while page i+1 is written (at most 3 ahead)
     settle (oldest review)   clean → the page is shown (scene.accepted, always in order)
                              not clean → roll back to page i: pages written after it are discarded, page i is repaired
       violation and attempts < 2 → repair_scene(i) · output critical → quarantine, regenerate once, then stop
       attempts spent → ship with the failure recorded (safety commitments never ship with a violation)
        │ story-level gate: schema, position balance, no repeats, lesson alignment
   illustrate (parallel, bounded)  TOOL per page → verify_image → retry once → degrade to text
   narrate (parallel)  TOOL per page → verify_audio → retry once → degrade
        │
   assemble_receipt  coverage, budget, degradations, ledger row, workflow attributes
```

- **State** (LangGraph): run id and seed, input hash, lesson and age, safety outcome and ignored text, character card, oath and hash, plan, accepted pages, rolling summary, attempt counters, the tool-call log (a plain list), verdicts, budget spent, degradations.
- **Context policy:** a page-writer call receives only a short oath summary, the card, beat *i*, a short rolling summary and the previous page's last line. On repair it also gets the failed verdict's expected and actual. Input tokens per page call should be flat from page 2 to 8: that curve in neatlogs is the evidence of context management.
- **Pipelining and the gate:** review latency is the largest cost (the judge is a slow reasoning model), so pages are written ahead while earlier pages are under review. This does not weaken the gate: a page is shown only after its own review is back and clean, in order, and a failed review throws away everything written after it. The last attempt at a page is always judged, so no page ships without its safety review.
- **Repair:** two attempts per node, each a new span with `repair_attempt`. Programmatic repairs where possible (position shuffle). A repair counts only if re-verification passes. An exhausted budget ships with the violation recorded; safety commitments never ship with a violation.
- **Safety tiers:** Tier A (visual danger) refuses with a calm message and a reason code only. Tier B (words in the drawing, harmless pixels) sanitises: the card is built from visual traits only, the text is recorded as ignored, and `no_drawing_text_obedience` is verified. Tier C (our own output trips the blocklist or the judge) quarantines the page and regenerates once, then stops. Any failure of a safety check itself is treated as Tier A (input) or Tier C (output).
- **Budget governor:** state carries `budget_usd` and `deadline_s`; if the projection exceeds the budget the run degrades non-safety checks first (judge sampling on quality commitments to 0, skip image checks, illustrate only key pages, text only). Every degradation is listed on the receipt.

## 5. Stack and decisions (verified 10 Oct 2026)

| Concern | Decision |
| --- | --- |
| Orchestration | LangGraph (Python 3.12). Our own client modules call the models; spans come from neatlogs decorators and `wrap` |
| API | FastAPI; `POST /stories`, server-sent events for progress; static web build served by the same app |
| Models: writer, vision, image, speech | Google Vertex AI, project `project-f0b6b4ce-541f-43ff-9f7`, location `global`: `gemini-3.7-flash` (writer, vision), `gemini-3.1-pro-preview` (reserve), `gemini-3.1-flash-image` (images), Cloud Text-to-Speech `gemini-2.5-flash-tts` (voice Kore) |
| Models: judge | K2 Horizon `IFM/K2-Horizon-375B-A23B` at `https://api.ifm.ai/v1` (OpenAI-compatible); a different family from the writer; a reasoning model, so budget extra tokens |
| AWS | us-east-1; EC2, Lambda, IAM roles, load balancers only; one instance per user; $25 team total; no Bedrock, Polly or S3. Optional hosting only |
| Auth to Vertex | Application Default Credentials; on this machine falls back to the signed-in `gcloud` account. No key files |
| Observability | neatlogs (project `482c3038-22f9-49e6-8938-e816ce252f75`) |
| Coding-agent memory | Entire (checkpoints, graph, Brain); `commit_linking: always` |
| Business plan | cfo.ai through its MCP server |
| Market data | Crustdata; raw data never enters the repo |

Model ids live in one config file so they can be swapped without touching the graph or the oath.

## 6. Observability (neatlogs)

- One trace per story: root `WORKFLOW` span `create-storybook`; node spans via `@neatlogs.span(kind="AGENT"|"TOOL")`; model calls via `neatlogs.wrap` on the Gemini and K2 clients (tokens, latency, cost); one `GUARDRAIL` span per verdict with `neatlogs.guardrail.input/passed/output` and our `neatlogs.eval.*` attributes; `neatlogs.log` for repair reasons.
- Identity: no `session_id` on one-shot stories; fixture id and lesson in end-user metadata.
- Detections (free plan allows five): critical safety, oath violation, lesson drift, image drift, injection obeyed. Cost and latency are alerts.
- Details and the verified API: `docs/neatlogs.md`.

## 7. Experiment and hardening loop

- **Two arms, same oath, same fixtures, same seeds.** `B0` observe-only: a single-shot 8-page generation, the oath evaluated afterwards, nothing gated or repaired. `B1` gate-and-repair: the graph above. Images and narration are stubbed in the bulk comparison.
- **Fixture matrix:** the drawing fixtures × four lessons × K runs per arm (start at K = 3).
- **Metrics from the ledger:** shipped-violation rate (stories that shipped with a broken non-critical promise), critical-stop correctness and false refusals, injection obedience, first-pass vs final pass rate, repair success rate, cost of gating (tokens, dollars, seconds, spans), context flatness, judge agreement on a human-labelled sample.
- **Hardening records** `HR-NNN` in `evidence/hardening/`: trigger trace, diagnosis, change (sha, Entire checkpoint id, prompt version), regression fixture, before and after numbers. We never stage failures; if the baseline is clean on a promise we say so.

## 8. Evidence system

- `evidence/ledger.jsonl` (append only, one row per named run), `evidence/traces/` (exported traces), `evidence/screens/` (timestamped screenshots), `evidence/entire/` (CLI outputs), `evidence/cfo/`, `evidence/hardening/`, `evidence/posts.md`. See `evidence/README.md`.
- `EVIDENCE.md` is generated from the ledger and these folders. A pre-submission linter checks commit dates against the window, checkpoint trailers, trace ids, detections fired, the cfo.ai link, secrets, posts and the video length.
- The machine clock is IST; use plain `date`.

## 9. Build milestones

| # | Milestone | Done when |
| --- | --- | --- |
| M1 | Scaffold, config, model clients, neatlogs init, ledger, spikes | a traced Gemini call and a traced K2 call; guardrail span nesting and attributes verified |
| M2 | Oath engine | verdict object, catalog, deterministic verifiers, judge with quote check, sampling, coverage; unit tests green |
| M3 | Graph and API | safety refusal and sanitise, card, oath, plan, page loop with repair, B0 arm, receipt, `POST /stories` with events |
| M4 | Images and voice | illustrate and narrate tools with retry and degrade, image and audio commitments |
| M5 | Web app | the screens in `docs/frontend.md` against `docs/API.md`, served by the backend |
| M6 | Evaluation | harness, B0/B1 sweeps, metrics, hardening records, generated `EVIDENCE.md`, linter |
| M7 | Business and content | cfo.ai model with measured cost, Crustdata market notes, posts, demo video |

Each milestone ends with a commit, an update to `docs/PLATFORMS.md` and a line in `hackathon.md`.
