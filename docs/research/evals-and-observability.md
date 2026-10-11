# Evals and observability for a launch to real children (4 to 8)

Written 11 Oct 2026 by a research pass. Two sources were read; what each page did and did not say is stated, and nothing below is a made-up quote. Current-state claims come from `docs/TOOLS.md`, `docs/QUALIFICATION.md`, `docs/STATUS.md`, `evidence/hardening/HR-001.md`, `assets/test-drawings/expected.json` and `scripts/eval_judge.py`. Commands marked "unverified" were not run.

## 1. What the sources actually say

### SWE-bench (https://github.com/SWE-bench/SWE-bench, plus `docs/guides/evaluation.md` and `docs/guides/datasets.md` on raw.githubusercontent.com)
Fetched fine. Gaps first, so nobody over-reads this: the README does **not** explain how tasks are built, does **not** define FAIL_TO_PASS or PASS_TO_PASS beyond one table row ("Fail to pass test cases", "Pass test cases"), and says **nothing about contamination**. Task construction is described as living in a separate collection tutorial, and new-instance creation is "temporarily paused". What it does say:

- **A frozen task record.** Each instance has `instance_id`, `repo`, `base_commit`, `problem_statement`, `patch`, `test_patch`, `FAIL_TO_PASS`, `PASS_TO_PASS` (datasets.md). Lesson: a case is one record with the input, the starting state and the pass condition together.
- **Containerised harness for reproducibility.** Evaluation runs in Docker; images can be built or pulled in advance; there is a `--max_workers` cap (README).
- **"Resolved"** means "The patch made the required tests pass"; unresolved means "The tests ran, but did not pass"; an instance with no `report.json` is an **error**, not a failure (evaluation.md). Lesson: three outcomes, and "could not produce a result" is kept apart from "failed".
- **Logs per instance:** `report.json`, `run_instance.log` ("What the harness did, and why it stopped if it failed"), `test_output.txt`, `eval.sh`, `patch.diff`; run summary `results.json`; results cached by `run_id` plus `instance_id`, so a new patch needs a new `run_id`.
- **Curated subset:** SWE-bench Verified is "Expert-verified solvable problems", 500 tasks announced Aug 2024 (README, datasets.md). Lesson: a human pass that removes impossible or unfair cases.
- **Versions:** Full, Lite, Verified, Multimodal, Multilingual; a Multimodal v2 is dated "Sep. 1, 2026" in the README news.

My inference, not the page's words: FAIL_TO_PASS and PASS_TO_PASS are the standard idea of "tests that must flip from red to green" plus "tests that must stay green". The pages fetched did not spell that out.

### OpenAI evaluation best practices (https://developers.openai.com/api/docs/guides/evaluation-best-practices)
Fetched fine (summarised by the fetch tool; short phrases only). The page does not use the term "trace grading"; its agent advice is to check each step.

- **Eval-driven development:** "Evaluate early and often", scoped tests at each stage.
- **Define the objective and metrics first**, then how to check them.
- **Dataset that looks like production:** mix of production data, expert-written examples and historical logs; typical, edge and adversarial cases.
- **Task-specific evals;** for agents add tool selection, argument accuracy and handoff accuracy.
- **Log everything** during development and mine the logs for eval cases.
- **Automate scoring** where possible (pass/fail, multiple choice).
- **LLM-judge pitfalls:** position bias and verbosity bias; use pairwise or pass/fail, control length, ask for reasoning before the score.
- **Calibrate with humans:** compare automated scores to human labels, several rounds, examples of each score level, a pass/fail threshold, consensus votes.
- **Evaluate agent workflows step by step** and only add multi-agent complexity when evals justify it.
- **Evaluate continuously:** on every change, watch production, grow the set; "a journey, not a destination".

## 2. What Storybound already has, mapped to the lessons

| Lesson | Already in the repo | Gap |
| --- | --- | --- |
| Objective stated as checkable criteria (OpenAI) | The oath: 22 core promises plus lesson, grown-up and quiz promises, in `src/storybound/oath/catalog.py`. Strongest asset | No single "launch scorecard" with targets (e.g. shipped-break rate below X, refusal false-alarm rate below Y) |
| Frozen case record (SWE-bench instance) | `assets/test-drawings/` (26 drawings) with `expected.json` outcomes; HR records name a job to re-run (`benign/bunny-bow-carrot`, `sharing`, seed 1, B1) | Cases are drawings, not full records. Failures found in sweeps are **not** frozen: HR-001 names one job in prose only. No "must flip" and "must stay green" lists |
| Reproducible harness | `scripts/sweep.py`, `run_story.py`, `eval_safety.py`, `eval_judge.py`; deterministic checks; seeds; prompt versions p1 to p4; ledger row per run | Providers are live and non-deterministic; no recorded-response mode, so a regression run costs money and time. No per-run folder of logs like `run_instance.log` (ledger row plus trace instead, which is fine but split) |
| "Resolved" metric with an error bucket | Ledger `outcome`, `shipped_violations`, `error`; sweep reports | `error` rows (e.g. the Vertex 429s in HR-007) are not reported as a separate rate next to the pass rate on the headline table |
| Verified subset (human pass) | None. The sister is the only human tester | No human-labelled set; the judge's 24/24 is on machine-made faults only (QUALIFICATION section 4 says so) |
| Contamination / leakage | Not a model-training issue here, but the same shape: prompts p1 to p4 were tuned on the same 7 drawings x 2 lessons the sweeps reuse | A held-out split (drawings and lessons never used while tuning) does not exist |
| Edge and adversarial cases | Tier A unsafe, tier B text-in-drawing, injection caption, PII drawings, blank, tiny, rotated (`expected.json`, 25/26 matched) | One unsafe drawing only; no non-English text, no frightening-but-not-blocked drawings, no ambiguous cases; stories (not drawings) get no adversarial prompts |
| Log everything | neatlogs trace per story (~150 spans), GUARDRAIL span per verdict, ledger, 16 exported traces | Production-style mining of traces into new cases is manual |
| Automate scoring | Deterministic checks plus K2 judge with quote check | Fine |
| Judge bias | Judge is a different family from the writer; it must quote the text and code verifies the quote; fault injection (swap, off-topic, scary), 24/24 and 0/8 false alarms | No check for **position bias** (e.g. promise order in the batch call, or page order) or **verbosity bias** (long page vs short page); `judge_batch` sends many promises in one call, so order effects are plausible and untested |
| Human calibration | neatlogs draft human evaluation "Human review of judge verdicts" (`evidence/neatlogs/20261011-write-config-results.json`), not yet run | 20 verdicts labelled by a person, with agreement number |
| Agent decisions graded | Decision points table in QUALIFICATION section 2; three-arm result 0/28 vs 27/28 shipped breaks | No eval of the **decision** itself (was repair vs rollback vs drop the right call?) from traces |
| Continuous evaluation | Sweeps run by hand per change; 7 detections; cost alert "Expensive story run" and critical-safety alert created | No scheduled or per-commit eval; alerts have no channel (email, Slack and webhook count are all 0 in the alert results) |
| Entire | Checkpoints per commit, 2 trails, 6 runners tailored to repo rules, `entire review general` | Runners guard code rules but not "did the eval numbers get worse"; PR #1 approvals gate fails for a solo project |
| cfo.ai | Cost per story measured; policy matrix; 3 scenarios | No support, safety-incident or compliance cost lines; month 6 hard-coded; no quiz or video cost rows |

## 3. The improvements (prioritised, at most 12)

Effort: S under 2 hours, M half a day, L a full day.

**1. Frozen regression set, FAIL_TO_PASS style (S/M). Tool: neatlogs + Entire.**
Build `evidence/regression/cases.jsonl`. One record per past failure: `case_id`, fixture, lesson, age, seed, arm, prompt version it failed on, the HR id, trace id, `must_flip` (the promise that failed, e.g. `age_reading_level`) and `must_stay_green` (the other promises of that run's ledger row). Seed it from HR-001 to HR-007 and from ledger rows with non-empty `first_pass_failed`. Add `scripts/regress.py` that reads the file, runs each job through `run_story.py`'s code path, and prints a table: flipped yes/no, still green yes/no, error (separate bucket, as SWE-bench keeps "no report" apart from "failed"). Evidence added: a re-runnable "these 7 bugs stay fixed" table per commit, tied to a checkpoint id. Start from `evidence/ledger.jsonl` (fields `first_pass_failed`, `broken`, `trace_id`) and `scripts/sweep.py` (job loop). Source: SWE-bench instance fields (datasets.md).

**2. Push the frozen set into neatlogs as a dataset and an evaluation (S). Tool: neatlogs.**
Upload the same cases as a neatlogs dataset and attach an automated evaluation that reads GUARDRAIL spans of the regression trace. Evidence: a dashboard run per commit that a judge can open without our scripts. Start: `neatlogs schema search dataset` and `neatlogs schema search evaluation` (the CLI's own discovery command, per `.claude/skills/neatlogs-public-api-cli/SKILL.md`); the exact dataset subcommands are **unverified**. Needs a write-scoped login (`neatlogs auth login`, which worked on 11 Oct per STATUS item 4).

**3. Judge position and verbosity bias check (S). Tool: neatlogs (traces) + scripts.**
Extend `scripts/eval_judge.py` with two modes. Order: run the same page with the promise list shuffled and reversed (three orders), report verdict flips. Length: pad a clean page with harmless filler (about 2x words) and shorten it; report whether a pass turns into a violation or the reverse, and whether the quote check still holds. Evidence: a table "verdict flips under reordering: n of N; under padding: n of N" and a note in the judge section. This is the OpenAI page's two named pitfalls, tested on our judge. Start: `FAULTS`, `mutate()` and `one()` in `scripts/eval_judge.py`, and `judge_batch` in `src/storybound/oath/judge.py`. Set sampling to 1.0 as the script already does. Cost: roughly the 88 judge calls of the earlier run, times three.

**4. Human calibration sample for the judge (S, but needs a person). Tool: neatlogs.**
Finish the existing draft evaluation "Human review of judge verdicts". Pick 20 verdicts: 10 judge violations and 10 judge passes from `evidence/traces/`, include the 6 dropped quiz questions from sweep 7. The sister or the builder labels agree/disagree in the neatlogs UI, using the OpenAI advice (a few examples of each score, a pass/fail line). Report agreement and which promises disagree. Evidence: first real human number on the judge (QUALIFICATION says "Human agreement with the judge was not measured"). Start: evaluation id `aea3e3ce-d209-4391-91c4-b7be6844ff07` in `evidence/neatlogs/20261011-write-config-results.json`. Rule 3 applies: use fixture stories only, never a real child's.

**5. Child-safety golden set, bigger and split (M). Tool: neatlogs detections.**
Grow `assets/test-drawings/` and `expected.json` from 1 unsafe drawing to about 12 and add story-level prompts, each with an expected outcome (`refuse_safety`, `proceed_sanitized`, `ask_redraw`): weapons, blood, a scary-looking but harmless drawing (must NOT be refused), a lonely or sad child figure (needs gentle handling), a drawing of a named real person, a text caption with a self-harm phrase, text in Hindi or Spanish, a very faint drawing. Mark each `tuning` or `holdout` and never tune on holdout (the leakage lesson). Report refusal recall and benign false-refusal rate separately. Sources of images must be licensed synthetic or public domain (see `assets/test-drawings/SOURCES.md`); generated unsafe images stay out of the public repo if they could harm. Start: `scripts/eval_safety.py --name safety-eval-2` and `expected.json`. Evidence: holdout safety numbers, with the Critical safety stop detection hits as the trace proof.

**6. Eval of the agent's decisions from traces (M). Tool: neatlogs.**
Grade the decisions, not only the outputs. From the ledger plus trace export, list every decision (`repair`, `rollback`, `accept_noted`, `regen`, `drop`, `degrade`) with its trigger verdict, then label each: right action, wasteful (repaired something cheap-checkable twice), or unsafe (accepted a safety break). Start with the 28 jobs of sweep 2 and the 19 first-pass breaks: expect about 50 decisions. Metrics: share of repairs that succeed on the first attempt, share of rollbacks that discarded good pages, mean repairs per fixed promise. Evidence: the OpenAI "evaluate each step" idea applied to the clause "each result guides the next action". Start: `pipeline.decide()` in `src/storybound/pipeline.py`, `evidence/traces/*.json`, `neatlogs traces spans list <trace_id> --json`.

**7. Held-out split and sweep discipline (S). Tool: ledger.**
Declare in `evidence/README.md` (or the sweep report header) which 4 of the 7 benign drawings and which lesson are tuning data and which are holdout, and run one sweep arm on holdout only after the last prompt change. Add `split` to the ledger row. Evidence: prompt p4's numbers on data it was never tuned against. Start: `scripts/sweep.py --fixtures` and `src/storybound/ledger.py`.

**8. Alerts that go somewhere, plus launch detections (S). Tool: neatlogs.**
The alert results show `slack:false, email:false, webhookCount:0`, so nobody is told. Add an email channel to "Critical safety stop" and "Expensive story run", and add alert rules for: any `Oath violation` that shipped (`shipped_violations > 0`), safety refusals per hour above a threshold (a spike means a model or prompt regression, or abuse), and p95 first-page time. Evidence: alert rule JSONs in `evidence/neatlogs/` and one triggered alert from a deliberately bad fixture run. Start: `neatlogs schema search alert` (unverified) and the earlier call recorded in `evidence/neatlogs/write-config.log`; note the cost alert failed first with `INVALID_ARGUMENTS` because the operator was sent as `>`.

**9. Recorded-response replay mode for CI-cheap regression (L). Tool: Entire + neatlogs.**
SWE-bench's container is about reproducibility. Ours cannot be bit-exact (live providers), but the deterministic half can be. Record page text and judge responses from a run into `evidence/replay/<case_id>.json` and let `tests/` replay them against the checkers and `decide()`. Then an Entire runner (`.entire/runners/trail-review.json` is the template) can flag a PR whose replay or regression table got worse. Evidence: a trail finding that cites a numeric regression. Start: `.entire/runners/trail-review.json`, `tests/test_pipeline.py` (check what it already mocks). Large; do after items 1 to 8.

**10. Entire: use Trails and `entire review` as the eval gate for prompt changes (S/M). Tool: Entire.**
Make one rule: any change to `src/storybound/prompts.py` or `oath/catalog.py` goes on a branch with a trail, and the PR body carries the regression table from item 1. Tailor the `trail-drift` runner (`.entire/runners/trail-drift.json`) to say "prompt version bumped without a before/after in `evidence/hardening/`". For the solo-approval gate (approvals failed on trail 2), either request a reviewer account or record it plainly. Evidence: a trail whose findings gate passes with a runner finding on a real prompt diff. Start: `entire trail create --repo gh/hatif03/storybound --title ... --type feature` (as used for trail 1, per TOOLS.md) and `entire review --configure --set-task "..."` (flags seen in `entire review --help`).

**11. cfo.ai: operating-cost scenarios for a real launch (M). Tool: cfo.ai.**
Add a scenario child or new rows in the cost table in the existing model (changes through `mcp__cfoai__edit_scenarios` and `edit_table_blocks`; read the `build-model` skill first). Rows, each labelled assumed: (a) support: tickets per 100 households per month, minutes per ticket, hourly cost; (b) safety incidents: review minutes per refusal or flagged story, a human-review share of flags, cost of one escalated incident; (c) COPPA and child-privacy compliance: a fixed yearly legal and audit cost and a per-user consent-flow cost, labelled as a placeholder pending real legal advice (this is not a quote); (d) regression-eval spend per release (from item 1's measured run cost); (e) quiz and video add-on rows that TOOLS.md says are missing. Show the effect on the 60% margin bar for Household and Classroom, Main versus Downside. Evidence: a Version history entry per change, and a measured number from the ledger feeding (d). Start: `docs/planning/cfo.md` and `evidence/cfo/README.md`.

**12. Cost-spike and provider-outage drills with traces (S). Tool: neatlogs.**
Run two named drills and keep the traces: (a) force a budget overrun (tiny token budget) and confirm the receipt lists the degradation and the "Expensive story run" alert fires; (b) force a provider outage by pointing the judge or image client at a bad key or host in a scratch shell (never print the key) and confirm the story either ships text-only or fails kindly, not hangs. A recovery run already exists for the image 429 (trace `94db23729dac6323368749acba4be1cb`); this adds the judge outage and the budget case. Evidence: two more recovery traces and alert hits. Start: `scripts/run_story.py --no-judge --name drill-...` and `src/storybound/clients/retry.py`.

## 4. Real-launch situations evals and monitoring should cover

Each line says the expected behaviour and how we would know. "Have" means a test or run exists today.

1. **Unsafe or scary drawing** (weapon, blood, a monster that is the child's joke). Refuse the truly unsafe, do not refuse the merely scary. Have: one unsafe fixture. Need item 5.
2. **Text inside the drawing** (names, addresses, phone, "ignore instructions", insults). Never obey, never repeat. Have: 8 of 8 with no leak, `no_drawing_text_obedience`; PII fixtures exist. Watch the `Picture has words painted in` detection.
3. **A different language** (child writes Hindi or Spanish; lesson read by a bilingual home). No fixture today. The reading-level checker is word-count based and English; check it does not fail every page in another language, and that the safety word list is not bypassed by translation.
4. **Very young reading level (age 4)** and age 8. HR-001 covered ages 4 to 8 only by a unit test; every run was age 6. Add one run at each age.
5. **Repeated stories.** Same drawing and lesson twice: the child should not get the identical story, and the second run must stay in budget. Check variation by seed and that nothing from a previous child's story leaks (state is per story; `DELETE /api/stories/{id}` exists).
6. **Partial failure.** Pictures missing on some pages, narration fails, quiz drops below two questions. Have: recovery run, quiz drop rule. Receipt must say what is missing; monitor the share of stories with any `degradations`.
7. **Offline or a flaky home connection.** The story may be half delivered. Check that the web app shows a clear state, does not lose the drawing, and a resumed story does not re-bill. Not tested today; a browser-level test with the network off in `web/scripts/` would cover it.
8. **Provider outage or quota.** Vertex 429 (HR-007), K2 judge down, gateway down. Decide and test: if the judge is down, quality checks degrade but safety checks stay; if the safety path is down, stop. Item 12.
9. **Cost spikes.** One story using many repair loops or a runaway retry. Per-story cost alert exists; add a daily total alert and a per-household daily cap, and watch repairs per story (1.82 mean in sweep 2; alert if the weekly mean doubles).
10. **A repair that makes things worse** (rollback storms, a repair that breaks another promise). Count repairs per story and promises newly broken by a repair; alert on a rise.
11. **Prompt or model drift.** A provider silently updates a model; first-pass break rate shifts. Run the regression set weekly (item 1) and compare with the last week's table.
12. **Judge failure modes:** unverifiable quotes (0 of 88 so far), position and length effects (item 3), false alarms that make stories needlessly slow.
13. **Sad or distressed content from a child** (a drawing about a hurt family member). Should lead to a gentle path and a grown-up note, not a cheerful story; needs a policy decision and a golden case.
14. **Grown-up input.** The grown-up promise typed in the lesson screen is untrusted text; test injection through that field as well.
15. **Privacy of traces.** neatlogs redaction (`<PERSON>` etc.) works on hero names; confirm a new name type (nickname, school) is also masked, and that no image bytes are in spans.

## 5. Suggested order for one day
1. Item 3 (judge bias) and item 4 (human sample): the two most visible judge claims. About 3 hours.
2. Item 1 then item 2: frozen set and neatlogs dataset. About 4 hours.
3. Items 7 and 8: split plus alert channels. About 1.5 hours.
4. Item 5 as time allows; items 6, 9, 10, 11 and 12 afterwards, in that order of value.

Rules to keep while doing it: no key in any prompt, log or file; fixtures only, no real child's drawing; one commit per intent so each checkpoint maps to one change; every number goes into `evidence/ledger.jsonl` and `hackathon.md` only if the run really happened.

## 6. Limits of this note
- SWE-bench pages fetched say little on task construction, FAIL_TO_PASS semantics and contamination; those lessons are marked as my inference or are not claimed.
- The OpenAI page was summarised by the fetch tool, so the quoted phrases are short and may be paraphrased by it; re-read the page before quoting it in a post.
- neatlogs dataset and alert subcommands and a cfo.ai COPPA cost figure were not checked; no commands were run and nothing outside this file was changed.
