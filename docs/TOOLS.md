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

### Trails (a trail is created; branch, PR and runners wait for a push)
- `entire runner setup --defaults-only` created the six trail runners (risk, confidence, drift, review, security, summary) with no model call. The **security, drift and review runners are tailored to this repo's hard rules** (no secrets, no child data, evidence discipline, the oath as the product, no timers or streaks for children) and committed under `.entire/runners/`.
- First attempt (before the builder enabled Trails on the dashboard): `entire trail create` and `entire review general` answered **"repository not found (404)"**.
- After Trails, Runners and Auto build were switched on in entire.io: `entire trail create --repo gh/hatif03/storybound --no-branch --title ... --type feature` **worked**. Trail **#1, ID `01M4MG92JRX974RCWS1FQ1ZWJ8`**, https://entire.io/gh/hatif03/storybound/trails/1 (evidence: `evidence/entire/20261011-0925-IST-trail-1-created.txt`). Per hack.entire.io section 06, each trail is backed by a GitHub PR and runners fire on push, so the next steps need a **push of a branch** (see STATUS.md). That push is blocked on purpose until the two pasted keys are rotated, because it sends Entire checkpoints whose transcripts contain them to GitHub; the permission check refused it and we did not work around it.
- `entire review` still needs a pushed branch to compare; not yet run.

### Result and limits (said plainly)
- Early work (the first ~13:00 to 14:30 IST of Saturday, M1 to M5 and the first sweeps) was done in a session started outside the repository, so it has **no checkpoint**; the HR-001 and HR-002 *change* commits (`04ffebb`, `daec9ea`) say so. `entire why` shows most older code as "human" for the same reason.
- **Keys in checkpoints.** Two keys were pasted into the session (a neatlogs key and the hackathon gateway key). Several checkpoints contain them; some are already on the private `origin`. Rotate both. Entire documents no way to remove a pushed checkpoint, so do not make the repository public with those refs until that is decided.
- The checkpoint link the submission needs is `https://entire.io/gh/hatif03/storybound/commit/<FULL_SHA>` plus the 26-character checkpoint id from the commit trailer. The repository is private, so a judge can open it only if added as a collaborator or the repository is public.
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
**Picture count, not verification, decides the margin.** In the policy matrix, every page illustrated fails the 60% bar on Main (43.4% in the first build), half the pages clears it, and text only clears it easily; sampled verification saves only about $0.002 per story. So the plan's recommendation is: **paint half the pages** (or cap stories per month) on the household plan, keep full verification. This went back into the product the same day as the **illustration policy** (`pictures: full | half | none` in the API and a grown-up setting; commit `dd3659c`): pages 1, 3, 5 and 7 are painted, the rest keep words and narration. That closes the loop the project set out to close: the business model sets a field in the agent's configuration.

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
