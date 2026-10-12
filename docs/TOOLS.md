# How neatlogs, Entire and cfo.ai were used

Written 11 Oct 2026. Every claim links to a file in this repository or says it is unverified. Numbers are the ones in `EVIDENCE.md` and `evidence/`; where a number is an estimate it says so. This document is about use: what each tool did for the project, what we tried, what broke, and what we could not do.

The three tools do three different jobs.

| Tool | Whose work it records | The question it answers |
| --- | --- | --- |
| **neatlogs** | The *story agent* and the *video agent* at run time | What did the agent do on this run, where did it fail, and did the fix work? |
| **Entire** | The *coding agent* (Claude Code) that built the project | Why does this code exist, which session and change produced it? |
| **cfo.ai** | The *business*: price, cost, margin, cash | What can we charge, what does it cost to serve, and which product setting should we run? |

The loop between them is the point: neatlogs found failures, each fix became one commit with an Entire checkpoint, and the measured cost that neatlogs produced went into the cfo.ai model, whose answer (paint half the pages) went back into the product as a setting.

---

## 1. neatlogs

### Architecture
- **One trace per story.** Workflow `create-storybook`: a `WORKFLOW` root, one `AGENT` span per graph node (safety, character, oath, write, verify, repair, quiz, media, receipt), `TOOL` spans for `illustrate` and `narrate`, `LLM` spans for every Gemini and K2 call (the clients are wrapped), and **one `GUARDRAIL` span per verdict** named `verify:<promise>`. A full gated story is about 150 spans.
- **A second workflow, `make-video`**, for the video agent: plan, narrate, build, check, render, repair, one guardrail span per video promise.
- **Server-side redaction** (`pii_enabled`, entities PERSON, PHONE_NUMBER, EMAIL_ADDRESS, LOCATION), because a drawing may carry a name or a number. Hero names therefore show as `<PERSON>` in exported traces.
- All of it lives in one module, `src/storybound/tracing.py`, which turns into a no-op if the key is missing so tracing can never break a story.

### Implementation
- Each verdict sets `neatlogs.guardrail.passed`, a status word, the score and the evidence quote on its span (`tracing.record`).
- **Seven detections** on the project: `Critical safety stop`, `Oath violation`, `Picture has words painted in` and `Quiz question failed a promise` (regex on GUARDRAIL output, created by us; the last two on 11 Oct, no hits yet) plus three defaults (`Expensive LLM Call`, `Slow LLM Response`, `Execution Failed`). `Oath violation` fired on a real overclaim in the video agent as well as on story pages.
- **Readback** through the neatlogs MCP server with `scripts/neatlogs_mcp.py` (tools used: `search_traces`, `get_trace_context`, `list_detections`, `triage_list`, `triage_get`). Free-plan traces expire after 14 days, so every named run's trace is exported to `evidence/traces/` (16 files) and its id is on its ledger row.
- **CLI** (`neatlogs-cli` 0.2.0, OAuth device login, read-only scopes) for `usage`, `evals`, `prompts` and `analytics`.

### Runtime: what the traces showed
- The recovery run: an image quota error (429) on four pictures, the story shipped with those pages as text only, and the receipt said so. Trace `94db23729dac6323368749acba4be1cb`, evidence `evidence/runs/20261010-1340-IST-kindness-rabbit-B1-media-image-429-recovery.json`.
- A repair: page 5 loses the hero's name, the check fails, the page is rewritten with only that failure as context, and it passes (trace `a32498d665231ab02f7218b8b54e9a3f` shows a reading-level repair; [HR-001](../evidence/hardening/HR-001.md)).
- The video agent catching an overclaim and repairing one scene: trace `3ec11cfc58c141c00b7119c53a05b821`.

### Reasoning: how traces led to fixes
Our rule is trace first (`CLAUDE.md`): find the failure in neatlogs, write the hypothesis, fix, compare runs. What that produced:

| Record | What the trace showed | Result |
| --- | --- | --- |
| [HR-001](../evidence/hardening/HR-001.md) | Reading level broke on most first-pass pages (trace `264208295ada9b28a96d2e29b32fb41c`, 7 repairs) | Writer told the limit: B0 pages over the limit 42.9% to 1.8% |
| [HR-002](../evidence/hardening/HR-002.md) | Review made gated stories slow | Pipelined review: total time -35% (mean) in a same-jobs ablation; time to first page did **not** improve, and the record says so |
| [HR-003](../evidence/hardening/HR-003.md) | The page writer sat at the limit and overshot by one word (trace `a32498d665231ab02f7218b8b54e9a3f`, scene 7) | Target two words under the limit: first-pass pages over the limit 13/112 to 1/112 |
| [HR-004](../evidence/hardening/HR-004.md) | neatlogs triage: "hurts" flagged critical | Mild terms now ask for a rewrite, not a stop |
| [HR-005](../evidence/hardening/HR-005.md) | neatlogs triage: one Gemini call per trace stalled 87 s | A 40 s timeout was tried, **did not hold up in an A/B, and was reverted** |
| [HR-006](../evidence/hardening/HR-006.md) | Found in the frames of the first story video, not by a check | New promise `image_no_text` |

**neatlogs's own triage.** neatlogs opened three issue cards on our workflow without being asked. We checked each against code, ledger and traces before changing anything ([TRIAGE-REVIEW.md](../evidence/neatlogs/TRIAGE-REVIEW.md)): one confirmed (the 87 s stall), one partly confirmed ("hurts" was a real false positive but nothing actually halted), one not confirmed (it read neatlogs's own `<PERSON>` redaction in trace text as if it were app behaviour).

### Result
- Measured cost per story, from the neatlogs API (`evidence/neatlogs/20261010-2010-IST-measured-vs-estimated-cost.json`): text and verification **$0.0097 (B0) and $0.0199 (B1)** per story; our own token estimate had been $0.0083 and $0.0162, about 20% low. This number replaced the estimate in cfo.ai.
- **What neatlogs does not measure:** it prices text only. For the two illustrated stories it reported $0.041 and $0.038, while our list-price estimate for pictures and voice is about $0.36. The cfo.ai model labels pictures and narration as assumed for that reason.

### What we tried that broke or did not work
- The `.mcp.json` server returned HTTP 401 in the editor session because `NEATLOGS_API_KEY` was not in that process's environment (a shell started from `scripts/dev-shell.ps1` had it). The helper script, which reads `.env`, worked throughout.
- `search_traces` with `fields` is not enabled yet (`NL-1923` rollout); keyword search matched 260 of about 1,200 traces, so per-run cost was read per trace id from the ledger instead.
- The MCP answers `429 MCP_SESSION_PROJECT_CAPACITY_EXCEEDED` when polled too fast (retry after about 80 s); the helper scripts back off.
- The CLI login gave **read-only scopes**, so evaluations, alerts, managed-prompt labels and sharing links cannot be created from the CLI; see "Not done" below.

### Not done (and why)
Human evaluations of the judge, alerts on cost or latency, guest links for judges, labelling prompt versions p1 to p4 as managed prompts: all need write access, which the CLI login does not grant; they are dashboard steps. The Claude Code plugin (captures coding sessions into the same project) was deliberately **not** installed: it records prompts and tool output, and a key was pasted into this session. Distributed tracing across the Node renderer was planned and not built.

---

## 2. Entire

### Architecture
Entire records the *coding agent*. CLI 0.11.4 with hooks installed for Claude Code, `commit_linking: always`, checkpoints synced to `origin`. Each commit made in a repo-rooted session gets an `Entire-Checkpoint` trailer; the checkpoint holds the session transcript, files and token use. `entire-graph` 0.4.0 (local, no network) and Entire Brain 0.1.0 (installed from the release, refreshed on a clean tree) add structural and memory views.

### Implementation
- One commit per intent so each checkpoint maps to one change. 40 or more checkpoints at the time of writing (`entire checkpoint list`). Every hardening record names the commit and its checkpoint id.
- **Graph evidence** (`evidence/entire/`): `graph diff` for the HR-001, HR-002, HR-003, HR-004 and HR-006 changes (the entities each fix touched), `graph impact` for `verify_scene_async` and `story_safe_text`, `graph verify` before and after.
- **`entire why`** on `src/storybound/oath/catalog.py` ties 18 lines to the checkpoint of the `image_no_text` change; on `pipeline.py` it ties lines to the HR-002 ablation switch.
- **Brain:** ten durable facts, among them "video specs never hold typed numbers", "a failure not tied to a scene stops the repair loop", and "a key pasted into a chat is recorded in checkpoint transcripts"; `brain brief` returns the likely files for a task.
- **`checkpoint tokens --compare`** between two checkpoints (`evidence/entire/20261010-1955-IST-checkpoint-tokens-HR-006-vs-HR-001-test.txt`); the tool itself warns that cache replay dominates the totals.

### Runtime and reasoning
The checkpoints are how a reader answers "why is this prompt this way": the HR commit messages carry the trigger, the trace ids and the before/after numbers, and the checkpoint carries the session that wrote them.

### Trails (two trails; trail 2 is backed by a branch and a PR)
- `entire runner setup --defaults-only` created the six trail runners (risk, confidence, drift, review, security, summary) with no model call. The **security, drift and review runners are tailored to this repo's hard rules** (no secrets, no child data, evidence discipline, the oath as the product, no timers or streaks for children) and committed under `.entire/runners/`.
- First attempt (before the builder enabled Trails on the dashboard): `entire trail create` and `entire review general` answered **"repository not found (404)"**.
- After Trails, Runners and Auto build were switched on in entire.io: `entire trail create --repo gh/hatif03/storybound --no-branch --title ... --type feature` **worked**. Trail **#1, ID `01M4MG92JRX974RCWS1FQ1ZWJ8`**, https://entire.io/gh/hatif03/storybound/trails/1 (evidence: `evidence/entire/20261011-0925-IST-trail-1-created.txt`). Per hack.entire.io section 06, each trail is backed by a GitHub PR and runners fire on push. The push was held back on purpose until the pasted keys were scrubbed from history (the permission check refused the first attempt and we did not work around it); the builder then approved a history rewrite, it was done on 11 Oct ([evidence/history-rewrite/NOTE.md](../evidence/history-rewrite/NOTE.md)), and the branch push went through.
- **Trail 2** (`01M4MK1J1NJYW4A4ZJ1DRQZEKD`, https://entire.io/gh/hatif03/storybound/trails/2) is backed by branch `docs/after-history-rewrite` and PR #1 on GitHub (the PR appeared by itself when the branch was pushed; checks: Entire Gates, GitGuardian Security Checks passed). `entire review general` ran on the branch against `main` with Claude Code: verdict "approve with nits", five findings (a real bug in `scripts/build_evidence.py` that printed the latest commit as the "First commit"; a missing exception for the approved rewrite in CLAUDE.md rule 1; stale Trails wording; a visibility wording gap; a missing PR reference). All five were fixed in the next commit. Gates on the trail (`evidence/entire/20261011-1030-IST-trail-2-gates.json`): checks passed (GitGuardian), up to date passed, **approvals failed** (the trail's rule wants one reviewer and does not allow self-approval, and this is a solo project), and the findings gate was still waiting for the `trail-review` runner. The PR is **open, not merged**: merging it is the builder's call (our permission check refused an unreviewed merge). Output: `evidence/entire/20261011-1010-IST-review-general-pr1.txt`, `evidence/entire/20261011-1010-IST-trail-2-show.json`.

### Result and limits (said plainly)
- Early work (the first ~13:00 to 14:30 IST of Saturday, M1 to M5 and the first sweeps) was done in a session started outside the repository, so it has **no checkpoint**; the HR-001 and HR-002 *change* commits (`04ffebb`, `daec9ea`) say so. `entire why` shows most older code as "human" for the same reason.
- **Keys in checkpoints, and the fix.** Two keys were pasted into the session (a neatlogs key and the hackathon gateway key). Entire had already masked the neatlogs key as `REDACTED`; the gateway key was in the text of three transcript files across many checkpoint-ref commits. Entire documents no way to remove a pushed checkpoint, so on 11 Oct, with the builder's approval, the history was rewritten with `git filter-repo` (key text replaced on every ref including `refs/entire/checkpoints/*`; the sister's drawings removed from every commit), and the rewritten refs were force-pushed one by one to the private `origin`. A fresh clone of the remote was scanned: 0 files contain any key value, 0 commits touch the removed images; `entire checkpoint list` and `explain` still resolve (checkpoint ids are not shas). New checkpoints now mask key shapes through `redaction.custom_redactions` in `.entire/settings.json`. Commit shas changed; the map is in `evidence/history-rewrite/sha-map.txt`. The keys must still be rotated, because GitHub may retain unreachable objects.
- The checkpoint link the submission needs is `https://entire.io/gh/hatif03/storybound/commit/<FULL_SHA>` plus the 26-character checkpoint id from the commit trailer. The repository was made public on 11 Oct after the rewrite. Anonymous check (clean headless browser): `https://entire.io/gh/hatif03/storybound/commit/1a96c19fd6f99c981f7e6b7cbbea715d25eb55d2` rendered the commit page with its checkpoint trailer `01M4MJM5TRM7NE2F8FHFJ49NE6` (`evidence/screens/20261011-1015-IST-entire-commit-link-anonymous.png`); a Log in button is visible but not required to read it.
- `brain refresh` refuses a dirty working tree (found by running it); `entire checkpoint explain --generate`, `entire dispatch` and `entire import` were not run (they spend model tokens or add pre-window history).

---

## 3. cfo.ai

### Architecture
The model answers one question: **what can we charge, what does it cost to serve, and which policy do we run.** Dimensions `Plan` (Household, Classroom), `Verification policy` (verify all, sampled) and `Illustration policy` (full, half, none). Month grain, Oct 2026 to Sep 2027. Scenarios Main, Growth and Downside (children store only their overrides). Pages: Assumptions, Unit economics, Verification and illustration policy, Cash and runway, Evidence and method. Built through the cfo.ai MCP from the design in [docs/planning/cfo.md](planning/cfo.md). Share link (read-only, no password): https://app.cfo.ai/s/vGE_ZEwfQtpoxPrg.

### Implementation
- Inputs are labelled **measured, derived or assumed** in the model. The single place a measurement replaces an estimate is the table "Cost per story inputs".
- **Measured cost replaced the estimate** on 11 Oct (change-log id **275839**): text and verification B0 0.0083 to 0.0097, B1 0.0162 to 0.0199, status "measured", with the basis cited ([evidence/cfo/README.md](../evidence/cfo/README.md)). Version history is the proof; the changelog export is `evidence/cfo/20261010-1745-IST-cfo-inspect-history.json`.
- Pictures (0.04 each) and narration (0.002 per page) remain **assumed list prices**, because neatlogs does not price those spans.

### Runtime: what the model says (month 6, estimates)
From the shared page, after the measured cost went in:

| | Main | Growth | Downside |
| --- | --- | --- | --- |
| Gross margin | 67.2% | 55.2% | 40.9% |
| Clears the 60% bar | yes | no | no |

On Main, month 6: Household 76.9% and Classroom 56.5%. Cash at the end of the window is positive in all three, but "runway" reads "not burning" only because fixed costs are $75 a month and nothing else is modelled: a limitation, not a finding.

### Reasoning: the decision the model made
**Picture count, not verification, decides the margin.** In the policy matrix, every page illustrated fails the 60% bar on Main (43.4% in the first build), half the pages clears it, and text only clears it easily; sampled verification saves only about $0.002 per story. So the plan's recommendation is: **paint half the pages** (or cap stories per month) on the household plan, keep full verification. This went back into the product the same day as the **illustration policy** (`pictures: full | half | none` in the API and a grown-up setting; commit `fa11e96`): pages 1, 3, 5 and 7 are painted, the rest keep words and narration. That closes the loop the project set out to close: the business model sets a field in the agent's configuration.

### Result and limits
- Anonymous check: the share link renders for a visitor with no cfo.ai session (headless browser, no cookies; screenshot `evidence/cfo/20261011-0845-IST-share-link-anonymous-render.png`). A dismissible "Keep your access" sign-in prompt appears; the workspace name "Invisible Technologies" is visible in the page title.
- Competitor price anchors in the model are approximate and come from app listings and secondary sources (see `docs/planning/plan-to-submission.md`, section 3).
- Month 6 is hard-coded as March 2027, and the text blocks quote figures as of the build; the quiz add-on (about +$0.004 per story, a token estimate from 26 stories) is noted in the basis text of the B1 cost row (change 279068) but is not a separate row, and the video add-on is not priced.
- Crustdata was used once, for a field-size note with **derived counts only** ([evidence/cfo/20261011-0850-IST-market-note-crustdata.md](../evidence/cfo/20261011-0850-IST-market-note-crustdata.md): of the 60 closest AI story products, 43 have 1 to 10 employees and 42 were founded in 2023 or later). It does not feed a number in the model. Raw Crustdata data must not enter the public repository.
- The workspace is on a trial that ends 24 Oct 2026; the builder has confirmed hackathon credits cover it.
- cfo.ai tool limits met: `dry_run` exists only on `create`, so updates had no dry run; a nested dimension layout produced a "one member's result" warning and was rebuilt with variable rows; no Version-history screenshot or workbook download could be made through the MCP (UI steps).

---

## 4. The other tools, briefly
Models and speech are not neatlogs, Entire or cfo.ai, but they shape what the three record: Vertex AI Gemini (`gemini-3.7-flash` writer and vision, `gemini-3.1-flash-image` pictures, Cloud TTS `gemini-2.5-flash-tts`), K2 Horizon as the independent judge (a different family from the writer; 24 of 24 injected faults caught, 0 of 88 judge calls unverifiable), and the hackathon LiteLLM gateway (Claude models answer in 1 to 2 s but caught 23 of 24, so K2 stays the judge: `evidence/runs/20261010-1823-IST-judge-eval-claude-*.json`). HyperFrames (Apache-2.0) renders the video: two renders of one scene were byte-identical and its `check` caught every defect we planted ([spike](../evidence/spikes/20261010-1720-IST-hyperframes-spike.md)).

---

## 5. Round two (Sun 11 Oct, afternoon): what the evaluation guides, the launch question and the child's hands changed
Prompted by two sources (SWE-bench's README and guides; OpenAI's evaluation best-practices page) and by asking "what if this launched to real children?". Reading notes, with what each page did and did not say: [research/evals-and-observability.md](research/evals-and-observability.md). Everything below ran; numbers are in the named files.

### neatlogs (measure the judge and the decisions, keep the traces)
- **Judge bias test** (`scripts/judge_bias.py`, `evidence/runs/20261011-1050-IST-judge-bias-1.json`): OpenAI names position bias and verbosity bias as the two judge pitfalls. Same 8 pages x clean / swapped-answer / scary variants (24 page runs, 72 promise verdicts, 0 judge errors), promises sent in three orders, and a variant with two harmless sentences added. **Clean pages: 0 flips.** The two promises that matter did not move: `story_safe_text` was critical on all 8 scary pages in every order, `correct_choice_teaches_lesson` caught the swap on every page in every order. All 9 flips (6 by order, 3 by padding) were on one borderline promise, `lesson_concept_in_scene`, on pages that were already faulted. One page, one lesson, one judge model: a small test, not a proof.
- **Frozen regression set** (`scripts/regress.py`, `evidence/regression/cases.jsonl`, SWE-bench's idea of one record per case with its pass condition): 16 past failures from the ledger, each with the promise that broke (`must_flip`), the prompt version, the sweep and the trace. Re-run on today's code (`regress-1`): **12 resolved, 3 unresolved (shipped with a break on the receipt), 1 error**, kept apart as SWE-bench keeps "failed" apart from "no result". The three unresolved are the hardest cases (reading level on honesty stories; a rewrite loop of 10 and 14 repairs). That is higher than the 1 in 28 of the last full sweep, as it should be for a set chosen from failures; but the run overlapped three other jobs (each story took 315 to 395 s instead of about 150 s), and **re-run alone, all three resolved** (`regress-2-alone`). So the honest reading is: with the machine busy the gate sometimes runs out of repairs on the hardest cases, and alone it did not. One run each. The error was a Vertex `499 CANCELLED` under load; it is now retried (HR-008), and the case re-ran clean on its own afterwards (one run, no load: this does not prove the cause).
- **Tuning and holdout** (`src/storybound/ledger.py`, every ledger row has `split`): the 7 drawings used while changing prompts are declared tuning; 5 never used in a story run are holdout (`holdout-1` sweep, HR-008).
- **Clip oath** (`scripts/clip_check.py`, HR-009): GUARDRAIL spans for a generated video clip, two judge families, the first Veo clip rejected.
- **Alerts:** besides the two earlier rules, four more rules were created from the existing detections after the builder's sign-in (oath violations seen, 3 in an hour; dropped quiz questions, 5 in two hours; words painted into pictures, 2 in two hours; slow story, p95 latency over 300 s), so **six alert rules exist** (`evidence/neatlogs/20261011-more-alerts-results.json`). The CLI login lasts about an hour, so each batch of write steps needs a fresh sign-in. No email or webhook channel is set because that sends an address to a service: the builder's call.

### Entire (rules that gate the next change)
- The drift runner now says: a change to `prompts.py`, `oath/catalog.py` or `oath/judge.py` needs a bumped prompt version, an `evidence/hardening` record with a before/after run and a regression table from `scripts/regress.py`, or drift goes up by at least 30. The review runner knows the small-hands rules (anything that deletes or abandons work must be a hold or undoable; no gestures of our own; browser storage is sessionStorage only and removed by Forget). The security runner flags key-shaped strings and any new vendor that would receive a child's drawing (`.entire/runners/`). They fire on the next pushed branch; none has run on these rules yet.
- Checkpoints still map one commit to one intent: the picture-agent change, the touch-safety change and the early-painting change are separate commits, each with its own record.

### cfo.ai (what a launch costs, beyond the model's three costs)
- New table **Launch operating costs (assumed, for real children's use)** on the Assumptions page (change-log ids 279306 and 279307): support tickets and minutes, human safety review of flagged stories, a placeholder for child-privacy compliance (not legal advice), the picture cost when Pip chooses (4 pictures, $0.16), and one video clip with a 1.4 retry allowance ($0.28). **All inputs are assumed.** With them, support plus safety review plus compliance come to about **$2.60 per household per month, 37% of the $6.99 Household price**. The point is sensitivity, not forecast: at launch scale (tens of households, not 500) a fixed compliance cost alone would exceed the price. The existing margin tables do not include these costs yet, so the 67.8% month-6 margin is the infrastructure margin only. Readback: `evidence/cfo/20261011-1215-IST-launch-operating-costs-readback.json`.

### What the touch work added to the evidence
`web/scripts/e2e-touch.mjs` (11 behaviours through a touch-emulating browser) and 7 unit tests; screenshots in `evidence/screens/`. Entire's review runner has not yet seen them.

---

## 6. Round three (Sun 11 Oct, afternoon): reading the platforms back, and using the credits
### neatlogs (a second pass through everything it holds)
Through the MCP with the project key (reads need no login): analytics views (kpis, cost, errors, time, tools, detections, waste, workflows), the detection list and trends, the triage list, trace search and trace context. Result in [research/neatlogs-incident-review.md](research/neatlogs-incident-review.md) (a 135-line review by a subagent, checked against the ledger): 2,095 traces, 110 error traces of which 58 of the 62 matched to the ledger still shipped (trace status "error" means a span errored, not that the story failed); the 87 s Gemini stall back in bursts; 9 of 13 critical safety stops were false positives on "hurt/fight" (all before HR-004) and 4 intended; two detections had never fired; no alert could notify anyone; model mix and tool error rates (`illustrate` failed 17 of 66 calls). Fixed or acted on in [HR-011](../evidence/hardening/HR-011.md): hedged retry for the stall, tiering of "ignore all", a quiz detection on GUARDRAIL spans, `STORYBOUND_TAGS`; the alerts were then retuned after the builder's sign-in (`evidence/neatlogs/20261011-alert-retune-results.json`): oath violation 40 an hour (it fired on nearly every story at 3), slow story p95 450 s, expensive story $0.10 on measured text cost, a new rule on the corrected quiz detection, and the blind "Quiz questions dropped" rule disabled. **Email delivery is on for all seven rules** and a real test alert was queued (`evidence/neatlogs/20261011-alert-email-results.json`). Delivery goes to each neatlogs user's own account email through their notification preferences (per user, not a typed address); no custom address can be set on a rule, and a webhook is the only way to reach another place. The three old triage cards were then handled through the MCP with the neatlogs team email (`evidence/neatlogs/review-2/triage_actions.json`): the PII card dismissed with a note (neatlogs's own redaction), the "hurts" card resolved (HR-004, HR-011), the latency card kept in progress until a real stall shows the hedge in traces. Still open: the picture-words detection and the orphan traces (HR-011 records what was tried: picture-verdict spans are missing from the story's trace, and a minimal thread-pool test attached fine).
### Entire (decisions, memory and gates)
Six Brain facts recorded (`entire brain remember`): Veo only in `us-central1`; the gateway's budget and routes; the small-hands rules; the eval gate; the neatlogs login limit; tuning versus holdout. A graph diff of the picture-agent, touch-safety and early-painting commits is in `evidence/entire/20261011-1300-IST-graph-diff-auto-pictures-touch-early-painting.json`. That change (model routing, the stall hedge, the soft-phrase tier) went on its own branch, [PR 2](https://github.com/hatif03/storybound/pull/2) and trail 3 (`01M4N0JMPVA2TP9JDGQBQQJ54K`). `entire review general` on it found **eight issues, all fixed** (`evidence/entire/20261011-1415-IST-review-general-pr2.txt`): no fallback when the gateway fails (a gateway outage would have ended a story at the planner), a hedge that left a stalled call in a non-daemon thread and counted its usage late, a 30 s hedge that could double slow-but-normal calls, an agreement script that counted error cells as passes, the quiz path still treating soft steering words as critical, an unknown gateway model priced at Gemini rates, and a bundled commit. **The cloud runners did not report**: after more than 30 minutes the findings gate on trails 2 and 3 still says "Waiting for the agent review of the current head" and the approvals gate fails for a solo project (`evidence/entire/20261011-1415-IST-trail-3-gates.json`); `entire review` run from the CLI is what produced the findings. The builder's screenshot of the repository settings on entire.io (11 Oct, 14:03) showed why: **Runners and Trails were on but "Auto build on push" was off**. The builder switched it on; on trail 4 (`01M4N27S2Z4W9Z99R7G2S2SBTJ`, branch `chore/cfo-workbooks-and-open-items`) the next push ran the `trail-review` runner: the findings gate **passed** ("Agent review found no blocking issues", head reviewed, 0 findings; `evidence/entire/20261011-1450-IST-trail-4-gates-runners-working.json`). The approvals gate still fails for a solo project.
### cfo.ai (video futures, a product plan, and the credits question)
Four scenarios under Main for video AI (3 Lite clips; a clip on every page, Fast; 3 standard 8-second clips; a 3-minute animated story) with the video cost folded into the story cost formula (changes 279505 to 279515), and a new page "Launch plan" with the real operating cost, one-time launch cost, contribution per household, break-even households and the price that breaks even at 500 households (279518, 279519). All assumed; numbers and reading in [BUSINESS.md](BUSINESS.md), readback in `evidence/cfo/20261011-1250-IST-video-ai-scenarios-and-product-plan-readback.json`. Credits: [CREDITS.md](CREDITS.md) and [HR-012](../evidence/hardening/HR-012.md). The whole narrative of how the three tools helped is [STORY.md](STORY.md).

---

## 7. Round four (Mon 12 Oct): experiments, failure drills, incidents and a human check
### neatlogs (incidents found, explained and resolved; one trace per story, whole)
- **Experiments and drills as traces.** Eight configurations and eight injected failures ran as tagged sweeps (`experiment`, `chaos`), so the dashboard could be read like a lab notebook; the ledger carries the configuration beside each trace id ([HR-014](../evidence/hardening/HR-014.md), [HR-015](../evidence/hardening/HR-015.md)).
- **Incidents it showed, and what we did.** The Claude Sonnet writer's three errors (opened in the error spans: a `choices` list where `correct` was expected) led to a tolerant parser and 10 of 10; the judge outage led to a failover judge from another family; a model outage shown as a refusal led to the try-again screen.
- **Its own incident cards, checked before fixing.** Three new cards opened on 12 Oct. We opened each card's linked traces: the "infinite repair loop" card linked three-span fragments (a tracing fault of ours, not a loop: the repair cap holds); the `illustrate` latency card was our own image-429 drill, recovered as designed; the K2 "prose" card was refuted by the span (valid JSON only). All three were resolved with notes (`evidence/neatlogs/review-3/triage_actions.json`). The fragments led to [HR-016](../evidence/hardening/HR-016.md): worker threads now start from the workflow's context, and the story's span has an input and an output.
- **Evaluations (human).** The first attempt added whole traces: the reviewer saw `{}` and `null`. It was closed and rebuilt as 17 single judge verdicts (3 violations, 14 passes), each opening on the promise, the page text and the verdict, with Agree / Disagree / Cannot tell and a reason; assigned to the builder. The result is the human-judge agreement, read from `evidence/neatlogs/review-3/` when answered; until then no agreement number is claimed.
- **Detections.** "Critical Violation Monitor" and "High Latency LLM Monitor" were accepted from neatlogs's suggestions; the picture-words detection now has spans to read (its pattern matches a violation and not a pass; it has not fired because no picture had painted words).
- **What cost time.** The CLI sign-in lasts about 15 minutes (we had assumed an hour), the trace export endpoint answered `SERVICE_UNAVAILABLE`, the evaluation form accepts `linear_scale` but rejected `rating`, and a multiple-choice question wants `options: {"options": [...]}`; the MCP helper kept working on the project key when the CLI login lapsed.

### Entire (one commit per fix; the review of this branch)
Each fix above is its own commit, so its checkpoint maps to one change (judge failover, tolerant parsing, the try-again screen, the span context, the story span's input and output). `entire review general` on PR 4 and the trail runner results are recorded in `evidence/entire/` (see the entry dated 12 Oct).

### cfo.ai (what the experiments cost, as inputs)
The measured cost of the experiment writers and judges (a Gemini Pro writer $0.113 a story, a Sonnet writer $0.122, a second judge $0.138, against $0.024 for the default) is in [CREDITS.md](CREDITS.md); it supports keeping the cheap writer plus repair in the cfo.ai cost basis. The model itself was not changed this round.
