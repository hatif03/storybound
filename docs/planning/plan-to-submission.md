# Plan to submission: what is left, why we are different, the business, the three tools, the story

Written Sat 10 Oct 2026, ~15:50 IST. Builds on [video-harness.md](video-harness.md) (the harness and its research). Facts below come from our own evidence or from the sources named; "unverified" means I could not confirm it.

## 0. Urgent, before anything else

1. **The neatlogs key you pasted in chat is on GitHub.** Three Entire checkpoints (`01M4JKQ263DXNS9BG84EV5X52E`, `01M4JKPTNVGR2HQR4QK8PEM4GR`, `01M4JKS425B02QFRAHTP1NRRM5`) contain it, and all five checkpoint refs are on the private `origin`. Rotate the key now. Entire documents no way to remove a pushed checkpoint, so **do not make the repo public** with those refs in it unless we first decide how to handle them (options in section 4.2).
2. **Deadline mismatch.** `CLAUDE.md` says submit Mon 12 Oct 19:00-23:55 IST. The Entire hackathon page says the event runs 10-11 Oct and lists no deadline. Confirm the real submission window on the official neatlogs post.
3. **cfo.ai billing.** The workspace is on a Startup annual trial that ends 24 Oct 2026 and then bills $375/month on a $4,500 annual term. Decide whether hackathon credits cover it, or cancel in Settings > Billing before 24 Oct.
4. **cfo.ai workspace name** is "Invisible Technologies" (empty, created by your account). Confirm it is the one for the judge-facing plan.
5. **Free-plan neatlogs traces expire after 14 days** and ingestion stops at 100k spans a month. Keep exporting to `evidence/traces/`.

## 1. What is left from the original plan

| Item | State | Cost to finish |
| --- | --- | --- |
| M1 to M3 oath engine, pipeline, API | done | none |
| M6 evaluation: sweeps, HR-001, HR-002, EVIDENCE.md, linter | done; HR-003 candidates open | small |
| M4 images and narration | built; one real run, 4 of 8 images lost to a quota error and recovered as text; **no measured cost for a full illustrated story** | one run, real money (about $0.2-0.5, estimate) |
| M5 web app | built, **never run on a real story**; touch, Safari, screen reader unverified | one session |
| Backend: "forget this story" delete endpoint | open | small |
| Parent- or teacher-written promises | open; the differentiator for classrooms | medium |
| HR-003 candidates: write under the word limit; "peach-colored" counted as one long word; the text-only fixture that flips between sanitise and redraw | open | small each, each with a before/after |
| M7 cfo.ai model with measured cost | not started | section 4.3 |
| Crustdata market notes (derived figures only) | not started | small |
| Video harness | planned, nothing built | section 5 |
| Demo video (at most 3:00), `#neatHack` posts (1 logged), submission post | not started | section 6 |
| Submission chores: Entire Trails form, repo visibility, checkpoint link and ID, key rotation | open | section 0 and 4.2 |

## 2. How we differ from a general-purpose agent

The sweep (84 runs, same drawings and lessons) is the evidence, because **B0 is a general agent and B2 is that agent reviewing itself**:

| Stories shipped with a broken promise | B0 plain writer | B2 self-review | B1 ours |
| --- | --- | --- | --- |
| `sweep-2-p2` | 27/28 | 27/28 | **0/28** |

What makes the difference, and what does not:

- **Not mainly safety.** The most common broken promises were the correct answer sitting in the same position, the lesson not appearing in the scene, and the lesson's own cues missing. Unsafe text was a handful of pages.
- **A contract first.** The oath is written per drawing and lesson, hashed, and checked page by page. A chat model has no promise to be held to.
- **An independent check.** Deterministic checks plus a judge from a different model family, with a quote check. Published work agrees that self-correction without external feedback often fails (Huang et al., ICLR 2024) and judges favour their own text (Panickssery et al., NeurIPS 2024). B2 behaved exactly so.
- **Repair is scoped.** A failing page is rewritten with only that failure as context, and later pages are rolled back (the pipelined review).
- **A receipt.** Parents, teachers and regulators can see what was checked. This matters now: COPPA amendments became fully enforceable on 22 Apr 2026, and the FTC opened a study in Sept 2025 of how AI firms test for harm to children (sources in the competitor notes below).
- **Editable promises** (to build): a teacher writes "the hero must share by page 5" and it becomes a judged commitment. A chat can agree to this; it cannot show it kept the promise.
- **Honest limit.** A well-built general agent could copy the idea. Our moat is the verifier catalogue, the measured evidence, and the receipt, not the model.

Competitors (competitor research, 10 Oct; mostly app listings and secondary sources): Gemini Storybook (18+ only, no child-safety claim, reviewers report anatomy and consistency problems; Common Sense Media rated Gemini's kid modes "High Risk" on 5 Sept 2025), DoodleTale (drawing to printed book, US/Canada), Readmio ($2.99 bundle), Oscar Stories ($4.99/month or $39.99/year), Wonderbly ($29.99+ per print book), Storywizard.ai (schools, quote-only, self-claimed filtering). **None publishes a per-page check or a parent receipt.** I found no published study of storybook promise violations, so our sweep is the only evidence of its kind.

## 3. Business model (to be decided inside cfo.ai, not by hunch)

Candidate lines, with the nearest price anchor:

| Model | Anchor | Main risk |
| --- | --- | --- |
| Classroom or teacher licence (lead with this: teacher-written promises are the differentiator) | adjacent tools about $5-13 per teacher per month (weak sources); no per-student price found | free incumbents, slow procurement, COPPA/FERPA proof |
| Household subscription | Oscar $4.99/month, $39.99/year | Google bundles a similar feature for free |
| Safety layer for other storybook apps (API) | generic moderation is nearly free | must sell oath-specific checks, repair and the receipt |

**The unit-economics question that decides the price:** text cost per gated story is about $0.016 (token estimate), but images dominate the total. The one partial media run (4 images, narration) was estimated at $0.19. If a full illustrated story costs a few tenths of a dollar (not measured), a $39.99/year household plan that allows many stories a week can lose money. So the model must choose among: a stories-per-month cap, sampled verification, a cheaper image model, or classroom-only illustrated stories. We need the measured cost of one full illustrated story before any margin is quoted.

## 4. The three tools: use them deeply, try what breaks, record what happened

Rule for every experiment: it produces a file in `evidence/`, a line in `hackathon.md` (what worked, what broke), and where it helps, a before/after.

### 4.1 neatlogs

Inventory from the docs index (https://docs.neatlogs.com/llms.txt): traces, session replay, comments, detections, **Investigate**, **Fixes**, analytics, experiments with managed prompts, **evals (human and AI)**, alerts, **guest links and sharing**, Claude Code plugin, OpenTelemetry and HTTP trace injection, **distributed tracing**, PII redaction, CLI with about 40 command pages, public API (about 230 operations). What we use: traces, guardrail spans, two detections, MCP/CLI readback, PII redaction (names show as `<PERSON>` in exported traces, which is working evidence for the no-child-data rule). The neatlogs research agent failed on a rate limit, so the table below is from the docs index plus our earlier verified notes in [neatlog.md](neatlog.md); plan limits are the public Free plan and unverified for hackathon credits.

| # | Experiment | Evidence it produces | Likely way it breaks |
| --- | --- | --- | --- |
| 1 | Register the writer prompts as **managed prompts** (p1, p2 as versions) so HR-001's change appears as a prompt version on traces | trace showing the prompt version; link in HR-001 | managed-prompt API only documented for templates; versions are integers |
| 2 | **Detections**: add the last free slot for the video harness ("Video promise failed"); check the two existing ones fired on sweep traces | detection hits listed in readback | 5-slot cap; condition detections need the right attribute keys |
| 3 | **Guest links / sharing** for judges (`neatlogs sharing traces get <id>`; guest links API) so judges open a trace without our login | a link in EVIDENCE.md, opened in a private window | enabling and URL shape not documented; expiry; free-plan gating |
| 4 | **Human evals** (free): rate 20 judge verdicts to measure judge-vs-human agreement; AI evals are not on Free | exported results (CSV/JSON) | time cost; form design |
| 5 | **Alerts** on a metric threshold (cost or latency per story) | an alert firing on a deliberately expensive run | thresholds on the right metric; notification channel |
| 6 | **Investigate** (3 a month): run one on the HR-003 failure and compare its diagnosis with ours | investigation text saved; agree or disagree stated | monthly cap, so use only on a real failure |
| 7 | **Distributed tracing**: continue the Python story trace into the Node renderer so one trace holds plan, TTS, render, verify, repair | one trace with the render spans nested | Node SDK or HTTP injection setup; context propagation |
| 8 | **Claude Code plugin**: capture coding sessions into the same project, next to the app traces | the build session of the harness visible as a trace | **records prompts and tool output**: only after the key is rotated, project-level hooks, never while pasting secrets; coding sessions add many spans against the 100k cap; the page documents no redaction |
| 9 | **Analytics** for measured cost per story to replace the cfo.ai input | analytics readback JSON | Gemini cost excludes thinking tokens (our earlier finding), so measured cost is understated; label it |
| 10 | **Session replay** and **comments** on the recovery run (`94db23729dac6323368749acba4be1cb`) | screenshot | none expected |

### 4.2 Entire

Findings from the Entire research agent (CLI 0.11.4; verified read-only): you are logged in; 6 checkpoints, 5 pushed; `entire why` links lines to checkpoints but most code shows "human" because early sessions were not run inside the repo (say so in the video); `checkpoint tokens --compare` works; `graph impact` works (3 callers, 9 callees on one function); `brain brief` works but its index is stale (run `entire brain refresh --agent none`). Trails, runners and auto build are flag-gated.

| # | Experiment | Evidence | Likely way it breaks |
| --- | --- | --- | --- |
| 1 | **Secret handling first**: rotate the key; set `redaction.pii.enabled: true` in `.entire/settings.json`; decide what to do about the three pushed checkpoints (a documented option is `--skip-push-sessions` for future ones; deleting a pushed ref with plain `git push origin :refs/entire/checkpoints/..` is standard git but not documented by Entire and unverified on entire.io) | a note in `hackathon.md` | no documented removal; the checkpoint id stays in commit trailers |
| 2 | **Accessible checkpoint link**: `https://entire.io/gh/hatif03/storybound/commit/<FULL_SHA>`. Private repo needs the judges added as collaborators and the GitHub App installed; public exposes all transcripts | link opened in a private window and as a second account; screenshot | 404 if the app is not installed; hourly permission sync |
| 3 | **Agent-improved proof**: `entire checkpoint tokens <HR-001 id> --compare <baseline>`, `graph diff` between the HR commits, paired with the neatlogs trace ids | files in `evidence/entire/` | cache replay dominates token counts; quote the caveat |
| 4 | **Trails**: submit the access form, have the repo admin (you) enable Trails and runners on entire.io, `entire runner setup --defaults-only`, commit `.entire/runners/`, `entire trail create` for the harness work | `trail show --json`, screenshots | flag approval latency; creates a PR; runners may need repo access |
| 5 | **Brain**: `brain refresh`, `brain remember` the harness invariants (claims must be source references, never literals), brief before, `entities history` after | before/after JSON | stale index; remember path format |
| 6 | **Review gate**: `entire review` on the harness change, `--findings` | findings file | spends model tokens (ask first); labs feature |
| 7 | **Dispatch and recap**: `entire dispatch --local --since 2d`; `recap` after push | markdown | spends tokens; hosted indexing delay |
| 8 | **MCP**: register `entire brain mcp` in Claude Code so memory is queried live; log the calls | call log | PATH on Windows |

### 4.3 cfo.ai

Report from the cfo.ai research agent (read-only; nothing created): MCP works; the workspace is empty; capabilities include dimensions, formulas, month-grain time, scenarios (child scenarios store only overrides), table comparison across scenarios, Canvas visuals (pricing-sensitivity, runway, scenario comparison), shareable read-only page links (no sign-in; revoke and password only in the UI), spreadsheet export (one sheet per table; charts and Canvas excluded), version history. Build order: update calendar; pages; "Plan assumptions" (Household, Classroom); "Cost per story inputs" by verification policy (the one place the neatlogs measurement replaces an estimate); customers; unit economics (revenue, inference, gross margin); cash and runway with a minimum-cash line; Growth and Downside scenarios overriding only what differs; comparison view; verification-policy view with an explicit margin bar (ours: at least 60% on Main at month 6); a price-sensitivity Canvas block; replace the cost input with the neatlogs number and keep the Version history screenshot; snapshot Main and Growth; share link for the judge-facing pages; export workbook, screenshots and history output into `evidence/cfo/`.

Try-what-breaks (each reversible through version history; always name the scenario): change Main and see Growth follow it, then override and see it stop; a circular formula with `dry_run` (cycles are not detected there); a step-function neatlogs bill pushed 10x; an unmapped coordinate read (the silent-zero trap) documented as a note; opening the share link in a private window and checking whether later edits show; a Canvas simulator at default sliders matching the Main baseline.

Inputs must be labelled measured, derived or assumed; no child data and no raw Crustdata rows go in (the export contains every input). Update the stale Bedrock and Polly lines in [cfo.md](cfo.md) to Vertex and Gemini TTS.

## 5. The video harness

Design, research and schedule are in [video-harness.md](video-harness.md). Decisions added today:

- Not MoviePy for the demo (no layout to check, no animation primitives); HyperFrames spike first; ffmpeg directly for the read-along export.
- The harness is itself traced (experiment 4.1 #7) and priced (cost per rendered video goes into cfo.ai as an add-on line).
- The demo video is produced from the final ledger, so every number on screen resolves to an evidence file, and the receipt says so.

## 6. The story for the judges

One sentence: **"Storybound keeps its promises to a child, and proves it, including where we were wrong."**

| Beat | Proof the judge can open |
| --- | --- |
| The problem: a model writes a story, and no one checks every page | Gemini Storybook reviews and the Common Sense rating (sourced) |
| We tested our own idea: 84 runs, 3 arms; plain 27/28 broken, self-review 27/28, gated 0/28 | `evidence/reports/` sweep-2, `EVIDENCE.md` |
| neatlogs found the failures: reading level on 90% of pages, then slow review | HR-001 and HR-002 with paired trace ids and exports |
| We corrected ourselves in public: the stale report, the confounded latency, the first-page time that did not improve | the same records |
| Entire shows why each fix exists | checkpoint ids, `entire why`, `graph diff`, the accessible link |
| cfo.ai turned the cost into a price and a verification policy | shared page, Version history, workbook |
| The harness applies the same thesis to the demo: no number on screen is typed by hand | the video's own receipt |

Demo structure and the five points per tool are in [pitch.md](pitch.md) section 6; fill its brackets only from the ledger.

## 7. Order of work

1. **Now:** rotate the key; confirm the deadline; confirm the cfo.ai workspace and billing decision.
2. **Sat evening:** one full illustrated story (measured cost) and one real story through the web UI; HyperFrames spike; neatlogs experiments 1-3; Entire experiments 1-2.
3. **Sun:** harness core, video oath, loop, tracing; first real harness failure becomes HR-003; cfo.ai model built and the cost input replaced; Entire Trails; neatlogs evals and alerts; teacher-written promises if time.
4. **Mon morning:** freeze code; generate the demo from the final ledger; `build_evidence.py`, `lint_evidence.py`; decide repo visibility; record link and checkpoint ids.
5. **Mon 19:00-23:55:** quote-post the submission.

Cut order if late: teacher-written promises, judged frame checks, read-along video, Trails. Keep: evidence, the cfo.ai plan, the receipt, the harness claim-sourcing.
