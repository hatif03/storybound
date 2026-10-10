# How Storybound uses neatlogs (v2)

> **Update 10 Oct:** the model stack is Google Vertex AI (Gemini) plus K2 Horizon as an independent judge; AWS has no Bedrock or Polly in this account (hosting only, $25 cap). See [plan.md section 0](plan.md#0-decisions-of-10-october). Wherever this file says Bedrock, Polly, Nova or Titan, read Vertex, Gemini TTS and Gemini image.

Instrumentation plan for the story agent and for the way we find and prove fixes. Companion to [plan.md](plan.md); [entire.md](entire.md) and [cfo.md](cfo.md) cover the other two required tools. Written 9 October 2026 from the live docs ([full bundle](https://docs.neatlogs.com/llms-full.txt)), re-verified against `plan.v1`'s [neatlog.v1.md](neatlog.v1.md). No application code: short API lines below are reference for the spikes, not project code.

neatlogs does two jobs here. It records what the **story agent** did, so a judge can open a run and see a commitment break and the agent respond. And it is the loop we use to **find, fix and prove** a failure: trace → Investigate or MCP → change → ledger rows that show the fix. Judges score whether it was used to build and improve the agent, not whether a badge was attached.

## 1. What the hackathon requires of neatlogs

From [neatlogs.com/hackathon](https://neatlogs.com/hackathon) and its FAQ (9 Oct):

- Every project uses neatlogs "with a clear role … in building the agent". The demo video must cover it on five points: **architecture, implementation, runtime, reasoning, result** ([plan.md §12](plan.md#12-the-three-minute-demo) maps each).
- Evidence: neatlogs trace links **or screenshots**; before/after "with the numbers you compared"; "a run where an action failed, showing what the agent did next".
- "All code must be written between October 10 and October 12." Installing the SDK and writing the first span happen after Saturday 12:30 IST. Today is accounts and docs only.
- The hackathon `neathack` skill ([neatlogs.com/hackathon/skill](https://neatlogs.com/hackathon/skill)): keep `hackathon.md` at the repo root with sections Project, Team, Stack, Build log, Demo, Known limitations and next steps, Submission; append a dated entry after each work session; record only tests that actually ran; link only "sanitized, shareable evidence"; never include keys, `.env`, personal data, private traces or tokens.
- v1 claimed a "setup prompt on hackathon/1" with a skill body to install at `.agents/skills/neathack/`. **There is no such prompt on the hackathon pages.** The setup prompt is the generic wizard "Prompt" tab ([quickstart/wizard](https://docs.neatlogs.com/docs/quickstart/wizard)). Where to keep the skill is our choice; we keep `hackathon.md`.

## 2. Corrections to v1 (verified against the docs)

| v1 claim | Fact | Source |
| --- | --- | --- |
| Regex detections match the guardrail output attribute | Regex detections match **span input/output text** (`input_pattern`, `output_pattern`). Attributes are matched by **Condition** detections | [Detections](https://docs.neatlogs.com/docs/features/detections), API detections |
| Set numeric attributes like `lesson_alignment_score` on the span | The only documented call is `span.set_attribute(k, v)` on the object yielded by `neatlogs.trace(...)`. There is no `set_attributes` and no get-current-span helper. Examples use `neatlogs.*` keys. A plain key is never shown | [Custom Attributes](https://docs.neatlogs.com/sdk/custom-attributes) |
| Prompt `version` labels `quest-v1`/`quest-v2` on templates | Templates have no documented string version. **Managed prompts** have integer versions and labels (`get_prompt`, `save_as_version`, `update_prompt`) | [Prompt Templates](https://docs.neatlogs.com/sdk/prompt-templates) |
| Experiments can run our Bedrock prompts | Playground is BYOK for OpenAI, Anthropic, Gemini, Azure OpenAI, xAI, Groq. No Bedrock. Datasets "coming soon" | [Experiments](https://docs.neatlogs.com/docs/features/experiments) |
| Tag the run with the lesson and fixture | Tags are process-wide only (`init(tags=…)`). Per-run metadata goes in `identify(end_user_metadata=…, session_custom_fields=…)` | [Tags](https://docs.neatlogs.com/sdk/tags), [Sessions](https://docs.neatlogs.com/sdk/sessions) |
| `pii_entities=["PERSON","EMAIL_ADDRESS"]` | The SDK setting accepts it and **persists it server-side** (changes the project setting). The detection-API PII entities are EMAIL_ADDRESS, PHONE_NUMBER, CREDIT_CARD, IP_ADDRESS, URL; no PERSON | [PII Redaction](https://docs.neatlogs.com/sdk/pii-redaction) |
| Seven detections, a classifier, previews, analytics export | Free plan: **5 detectors**. Detection preview, suggestions, analytics export, classifier workflow and historical rescoring are **disabled in production via the public API** (as of 6 Oct 2026) | [Release workflows](https://docs.neatlogs.com/cli/release-workflows), [Availability](https://docs.neatlogs.com/api-reference/availability) |
| A second `init` with another workflow raises | The docs conflict: the wizard prompt says raise, `/sdk/multiple-workflows` says no-op. **Never call it twice.** Label roots with `root.set_attribute("neatlogs.workflow_name", …)` if ever needed | [Multiple Workflows](https://docs.neatlogs.com/sdk/multiple-workflows) |
| No `langchain` extra | `pip install -U "neatlogs[langchain]"` is the documented extra; the **handler** is still the only activation path | [Python SDK](https://docs.neatlogs.com/sdk/python) |
| A shareable trace URL | **Not documented how to create one.** Public sharing exists (`GET /api/v1/public/traces/{id}/sharing` returns `enabled`, `state`, `expiresAt`; CLI `neatlogs sharing traces get <id>`). Enabling and the URL shape are spike S4 | [Sharing API](https://docs.neatlogs.com/api-reference/endpoints/traces) |
| Cursor | Not documented for neatlogs plugins. The team uses **Claude Code** | [Claude Code plugin](https://docs.neatlogs.com/integrations/claude-code) |
| The `workflow_name` should be `create-storybook` | Unchanged. It names the task, not the repo | [Workflow Name](https://docs.neatlogs.com/sdk/workflow-name) |

Things v1 had right and we keep: handler built once and passed at `invoke`; init before importing LangChain and boto3; `sample_rate=1.0`; no `session_id` on one-shot stories; flush and shutdown once in the server lifespan; Python 3.11+; MCP with `ping` then `whoami`; Doctor twice.

## 3. Free-plan limits and what they force

Per the builder, hackathon participants get **special credits for neatlogs, Entire and cfo.ai from kickoff**; the terms are not yet published. The table below is the **public Free plan**, kept as the planning baseline: if the credits lift a limit we gain slack, and if they do not the design already fits. From [neatlogs.com](https://neatlogs.com) pricing:

| Limit (Free) | Plan response |
| --- | --- |
| 100k spans/month, **hard cap** | Span budget below; keep a 20% reserve; check the dashboard before each sweep. When the cap is hit, ingestion stops and evidence is lost |
| 5 detectors | The five chosen in §8. Cost and latency go to **alerts** (metric threshold), not detectors |
| 3 Investigations/month | Reserved for the first two hardening records; MCP triage reads are not Investigations |
| 2 users | Not binding: we are solo, one seat |
| 14-day retention | Export every named run to the repo within hours (§9). Traces die around the 16 October results |
| AI evaluations not on Free (Starter: 5,000) | Human evals only (unlimited on Free). They fit the judge-agreement sample |
| Trained classifiers not on Free | Built-in `nsfw`/`hate` classifier detections: try in the dashboard; they may consume a detector slot |
| 1 project | One project, `storybound`. No second project for the traffic script or for coding-session traces |

Winners get 3 months of Pro. No Pro credit for participants is listed. If the span cap or retention bites mid-weekend, one month of Starter ($99) is the fallback; decide before Sunday.

**Span budget.** One full B1 story: ~150 spans (a GUARDRAIL span per commitment per scene dominates: ~8 scenes × ~8 commitments, plus node, LLM, tool and LOG spans). B0 ~50. The 72-run matrix at K = 3: 72 × (150 + 50)/2 ≈ 7–11k spans. A full real-image demo story is the same ~150. 100k spans ≈ 650 full stories. LOG spans from `neatlogs.log` count; use them for repair reasons only.

## 4. Setup order

All in the new repo, after the first commit, except accounts (today).

1. **Today:** sign up at [app.neatlogs.com](https://app.neatlogs.com); one project `storybound`; ingest key from Settings → API Keys. Store as `NEATLOGS_API_KEY` in a gitignored `.env`. Install the CLI: `npm install --global neatlogs-cli@0.2.0` (Node 22 or 24). `neatlogs profile set work --host 'https://app.neatlogs.com'`, `neatlogs auth login`, set the project, `neatlogs whoami`.
2. **Python 3.11 or 3.12.** The SDK needs ≥ 3.10 and < 3.14; async LangGraph on 3.10 loses nested LLM callbacks unless every node forwards `config`.
3. **Skills** (project-local, so Claude Code instruments from current docs, not memory): `npx skills add neatlogs/skills --skill "neatlogs-py"`, plus `neatlogs-py-langchain` for the LangGraph path and `neatlogs-public-api-cli` for the CLI and API. Source: [github.com/neatlogs/skills](https://github.com/neatlogs/skills).
4. **SDK:** `pip install -U "neatlogs[langchain]"` (add `[bedrock]` only if we `wrap` a boto3 client).
5. **Do not run the full wizard** (`npx @neatlogs/wizard`) on the application. The wizard prompt itself says to hand-instrument from the SDK page. Use the wizard only for MCP.
6. **Doctor, twice.** `python -m neatlogs doctor --local --json` (capture only), then with the key in the environment `python -m neatlogs doctor --probe --json`. Neither replaces one real story trace.
7. **MCP:** `npx @neatlogs/wizard mcp --api-key <project key>`, or add a server to the Claude Code MCP config: Streamable HTTP, `https://ingest.neatlogs.com/mcp`, `Authorization: Bearer <project key>`. Call `ping`, then `whoami`; if they fail we are not "using MCP". Do not commit the config if it carries the key.
8. The public API and CLI automation need a separate credential (service account), not the ingest key. We use dashboard configuration unless the credential is in hand; nothing blocks on scripting detections.

## 5. Initialisation and lifecycle

One process, one `neatlogs.init`, at startup, after `load_dotenv()` and **before** importing LangChain, LangGraph or boto3.

| Argument | Value | Why |
| --- | --- | --- |
| `workflow_name` | `create-storybook` | The task, not the repo |
| `sample_rate` | `1.0` | A dropped trace is a missing judging artefact. Sampling is an oath concern, never a tracing one |
| `capture_logs` | `True` | `neatlogs.log("repair {node} {attempt}", …)` becomes a LOG span, so the reason sits on the timeline. Must run inside an active span or it is dropped |
| `pii_enabled`, `pii_entities` | on; email, phone | Fixtures are fictional, redaction stays on. Note: persisted to the project |
| `debug` | `True` during the build; off for the recording | stderr noise |
| `tags` | `["storybound", "<git sha short>"]` | Process-wide only. The sha ties a trace to a commit without a ledger lookup |
| `instrumentations` | omitted | LangChain is not listed here. One mechanism per call |

FastAPI is long-running: the exporter flushes in the background. Call `flush()` and `shutdown()` once in the lifespan shutdown, not per request ([Flush and Shutdown](https://docs.neatlogs.com/sdk/lifecycle)). The eval harness that imports the graph directly is a script: it inits, runs, then `flush()` and `shutdown()`, or its spans die with the process. `/health` never touches the SDK.

## 6. One trace per story

`POST /stories` is the trace root, a `WORKFLOW` span named `create-storybook`. The handler is built **once** at startup (`neatlogs.langchain_handler()`) and passed at invoke time: `config={"callbacks":[handler]}`. A new handler per request splits the trace. Attaching it inside a node on `llm.invoke` orphans LLM spans ([Multi-Agent LangGraph](https://docs.neatlogs.com/guides/multi-agent-langgraph), [LangChain](https://docs.neatlogs.com/integrations/langchain)).

**Identity.** A story is one shot, so no `session_id` (neatlogs then sets it to the trace id). Per-run fields go through `identify`:

- `end_user_id`: the fixture id (`fx-bunny`, `fx-evilcat`, `fx-killfish`), never a real child.
- `end_user_metadata`: `lesson`, `arm` (B0/B1), `seed`, `run_id`.
- `session_custom_fields`: `fixture_id`, `entry_point`. Whether these work without a `session_id` is **spike S6**; the fallback is `end_user_metadata` alone.

Only if the adaptive path ships ([plan.md §7.7](plan.md#77-adaptive-path-p2-stretch)) do turns share a `session_id` equal to the story id, each turn its own trace.

### 6.1 The span tree

Node spans come from the handler. Oath steps are ours, because the handler does not know what a commitment is.

| Span | Kind | Source | A judge should see |
| --- | --- | --- | --- |
| `create-storybook` | `WORKFLOW` | decorator on the route | One root; `contract_coverage_pct`, `outcome`, `oath_hash` as attributes |
| `intake`, `safety_screen`, `vision_character`, `oath_author`, `story_planner`, `scene_writer`, `repair_scene`, `illustrate`, `narrate`, `assemble_receipt` | node spans | LangGraph handler | Inputs, outputs, nested LLM spans |
| Gemini (Vertex) and K2 calls | `LLM` | handler from `usage_metadata` | Model, prompt, completion, tokens, latency, cost |
| `analyze_drawing`, `screen_drawing`, `generate_image`, `synthesize_speech`, `apply_guardrail` | `TOOL` | `@neatlogs.span(kind="TOOL", tool_name=…)` closest to `def` | Tool name, args, result, error |
| One span per commitment check | `GUARDRAIL` | `with neatlogs.trace(<commitment>, kind="GUARDRAIL") as span` | Passed or Blocked, the verdict object, nested under the node that produced the checked thing |
| Repair | the same node, new spans | graph edge | `repair_attempt` and the failed verdict in a LOG span |
| Refusal | workflow ends on a critical guardrail | no repair edge | `neatlogs.guardrail.passed=false`, output beginning `CRITICAL:` |

B0 (observe-only arm) produces the same span kinds but never a repair span and ends with post-hoc guardrail spans.

Decorator order when a function is also a framework tool: the framework decorator above, `@neatlogs.span` closest to `def`.

### 6.2 Model calls: one mechanism per call

Default plan: text and vision through LangChain's Bedrock chat model inside the graph with the single handler; image generation and Polly as `TOOL` spans around boto3. **Do not also `neatlogs.wrap` a client that the handler already sees** (double counting). The docs' Bedrock page covers `neatlogs.wrap(boto3.client("bedrock-runtime"))` only; LangChain-Bedrock is not mentioned there, and token usage through LangChain comes from `usage_metadata`. Cross-region ids look like `us.anthropic.claude-…`, not the bare model id. **Spike S2** decides between the handler path and a `wrap` path based on one real trace.

## 7. Guardrail spans, exactly

Per [Custom Attributes](https://docs.neatlogs.com/sdk/custom-attributes) the dashboard shows Passed / Blocked from these three attributes:

| Attribute | Value in Storybound |
| --- | --- |
| `neatlogs.guardrail.input` | The text or JSON the commitment looked at (the scene, the card, the image prompt), truncated |
| `neatlogs.guardrail.passed` | `true` only for status `pass`. `warning`, `violation`, `critical`, `verification_error` are `false`. A `skipped` (sampled out) is a LOG line, not a failed guardrail |
| `neatlogs.guardrail.output` | `STATUS: expected … / actual …`, beginning with the status word in capitals: `PASS`, `WARNING`, `VIOLATION`, `CRITICAL`, `VERIFICATION_ERROR` |

Because regex detections match span input/output **text**, and the SDK may expose `neatlogs.guardrail.output` as an attribute rather than as the span's `output.value`, spike S3 checks which one a regex detection fires on. If only `output.value` is matched, the `with` block also returns the status line as the span's output.

Further attributes on the same span (all under a prefix; `neatlogs.eval.` is the working hypothesis, verified in S3 on one real trace before cloning the pattern):

```text
neatlogs.eval.commitment          stable id
neatlogs.eval.scope               run | story | scene | image | audio
neatlogs.eval.status              the Sworn status word
neatlogs.eval.verdict_by          deterministic | judge | both
neatlogs.eval.sampled             true | false     neatlogs.eval.seed
neatlogs.eval.judge_model         family and id
neatlogs.eval.score               0..1 where a judge scored
neatlogs.eval.lesson_alignment_score   neatlogs.eval.image_match_score
neatlogs.eval.attempt             0, 1, 2
neatlogs.eval.evidence_quote      judge's verbatim quote (truncated)
```

Workflow root: `neatlogs.eval.contract_coverage_pct`, `neatlogs.eval.oath_hash`, `neatlogs.eval.outcome`, `neatlogs.eval.budget_used_usd`. These are the same fields as the ledger row ([plan.md §10.1](plan.md#101-the-run-ledger)). The observer writes both from one verdict object, so they cannot diverge.

`NeatlogsObserver` keeps Sworn's three-method shape: capture the current span, submit an evaluation (open and fill a GUARDRAIL span), submit coverage. No other module imports neatlogs.

## 8. Detections, alerts, evals

Configuration in the dashboard, after the first real traces exist so previews (if the dashboard has them) and field names match. They do not change the agent; the oath does. They make the oath filterable in the traces list.

**Five detectors** (Free limit):

| # | Name | Type | Rule | Replaces (Storytopia) |
| --- | --- | --- | --- | --- |
| 1 | `critical-safety` | Regex on span output | `^CRITICAL:` | Inappropriate-content spike. Infra failures no longer count (S3 in plan §5.2) |
| 2 | `oath-violation` | Regex on span output | `^VIOLATION:` | The pass/fail monitors |
| 3 | `lesson-drift` | Condition | lesson alignment score `< 0.6` | Lesson prompt drift |
| 4 | `image-drift` | Condition | image match score `< 0.7` | Visual consistency degradation |
| 5 | `injection-obeyed` | Regex on span output | `VIOLATION: no_drawing_text_obedience` | New: the "Kill fish" fixture |

Built-in PII detection is a project/SDK setting, not one of the five. A built-in `nsfw` or `hate` classifier may be tried if a slot or the plan allows; the API route for classifiers is disabled in production, so try the dashboard only.

**Alerts** ([Alerts](https://docs.neatlogs.com/docs/features/alerts)), server-side, no code: per-event on `critical-safety` (severity critical, email or in-app); metric thresholds on workflow latency and cost per story (provisional $1.80 and 18 s from Storytopia until Bedrock numbers exist, replaced from the first real sweep and the cfo.ai model); cooldown on so a sweep does not page us for every fixture. The evidence for the cost/latency family is the alert history, since cost and latency do not use a detector slot.

**Evals** ([Evals](https://docs.neatlogs.com/docs/features/evals)). Free plan: human evaluators, unlimited. We use them for the **judge-agreement sample** ([plan.md §8.3](plan.md#83-verification-mechanics)): 30–40 scene verdicts are shown to a human ("is the lesson in this scene? yes/no"; "safe for a 4–8-year-old? yes/no"). Export the batch (CSV/JSON) into `evidence/`. An AI evaluator with an oath-shaped rubric is P2 and needs Starter.

**Investigate and Fixes** ([Investigate](https://docs.neatlogs.com/docs/features/ai-search), [Fixes](https://docs.neatlogs.com/docs/features/triage)). On a hardening record's trigger trace, ask Investigate why the commitment failed; read the suggestion in Claude Code through MCP `triage_get` and `triage_get_investigation`. Apply the change locally. Cloud dispatch to a GitHub PR is optional and needs the GitHub integration. After the next ledger rows show the fix, `triage_accept` and `triage_update_status`.

## 9. Prompt versions

The before/after must be visible in the trace, not only in git. We use **managed prompts**: `neatlogs.get_prompt(name, label="production")`, and change a prompt with `save_as_version(prompt_name=…, messages=…, labels=…, commit_message=…)` and move the `production` label with `update_prompt`. Versions are integers, so "quest v2" means managed version 2, and the ledger stores `prompt_versions`. The prompt text we ship in the repo and the managed prompt are kept identical (a test compares the hash). Fallback if managed prompts do not behave in S2: distinct span names (`quest_prompt`) with `SystemPromptTemplate`/`UserPromptTemplate`, plus the git sha tag. Only two or three prompts are managed: writer, oath author, judge.

## 10. MCP and CLI during the build

| Tool | When |
| --- | --- |
| MCP `search_traces` | Find a run by fixture id or by `VIOLATION` |
| MCP `get_trace_context` | Read a span tree, inputs, outputs and which detection fired, without opening the dashboard |
| MCP `list_detections`, `get_detection_trend` | Confirm rules exist and the sweep triggered them |
| MCP `triage_list`, `triage_get`, `triage_get_investigation` | Pull the fix brief into the editor |
| MCP `triage_accept`, `triage_update_status` | After the fix is proven |
| CLI `neatlogs traces list\|search\|get`, `traces spans list <id>`, `traces payload <id> <span> --fields input,output,error`, `traces evaluations <id>` | Scripted evidence and the ledger backfill |
| CLI `neatlogs traces export <id> --format markdown\|json\|csv` | **Evidence that survives retention** |
| CLI `neatlogs analytics kpis\|cost\|chart\|facets` (max 30-day window) | Cost and latency numbers for [cfo.md](cfo.md) |
| CLI `neatlogs usage` | Span usage against the 100k cap |
| CLI `neatlogs sharing traces get <id>` | Is a trace publicly shared (S4) |

`log_trace` is not how the app sends telemetry; the SDK does that. A hand-built trace via `log_trace` would be a second, fake source, and we will not use it.

## 11. Evidence: exports, links, screenshots

- **Trace id into the ledger.** Spike S4: find how to read the current trace id in-process (the span object from `trace()` is the likely route). Fallback: per-run id in `end_user_metadata` and a backfill script that resolves trace ids with `neatlogs traces search`.
- **Public link.** The docs do not describe a UI toggle. Spike S4 looks for a Share control on the trace page and confirms with `neatlogs sharing traces get <id>`. Guest links are for evaluation reviewers (`neatlogs guest-links mint --evaluation …`), not trace links.
- **Export and screenshot every named run within hours**, into `evidence/traces/` and `evidence/screens/`, after removing anything private. `neatlogs traces export <id> --format markdown` and `--format json`. Screenshots are explicitly acceptable evidence per the hackathon rules, and they are what survives the 14-day retention.
- Example trace URLs in the MCP docs (`https://neatlogs.com/traces/tr_…`) are examples only; do not assume that shape is a public link.

## 12. What the video says about neatlogs (five points)

1. **Architecture:** handler for LangGraph nodes and LLM calls, decorators for tools, GUARDRAIL spans for commitments, one observer module.
2. **Implementation:** the three guardrail attributes and the eval attributes; managed prompt versions.
3. **Runtime:** the tree for one story; the red scene, the repair spans, the green re-check; tokens flat across scenes; the detection firing; the cost and latency alert.
4. **Reasoning:** Investigate or MCP naming the cause of the hardening record; why detections key off the oath.
5. **Result:** B0 vs B1 shipped-violation rate (k of n), p50 and p95 latency and cost of gating, from the ledger and from neatlogs analytics.

## 13. Practices that keep the evidence intact

- One mechanism per model call. Handler for LangChain; `wrap` only for a boto3 client LangChain does not see.
- `init` once, before the imports. Handler once. `sample_rate` 1.0.
- No `session_id` on one-shot stories.
- A GUARDRAIL span per verdict with the three attributes and a status word at the start of the output text.
- Prompt versions change when prompts change.
- Doctor probe, then one real story, then detections. A green install is not a trace.
- Keys in the environment or a gitignored `.env`. Never in a prompt: Entire checkpoints store prompts.
- No real child data anywhere. Fixtures are fictional or attributed sample drawings.
- Count spans before every sweep.

## 14. Verification checklist for the spikes (S2, S3, S4, S6)

- [ ] A hand-made trace with a node span (handler), an LLM span with tokens and cost, and a GUARDRAIL child: nesting correct, no duplicate LLM span.
- [ ] A custom numeric attribute appears in the span and a Condition detection on it fires.
- [ ] A regex detection fires on a guardrail span whose output begins `CRITICAL:`; note whether it matched the attribute or `output.value`.
- [ ] The trace id is available in-process, or the backfill path works.
- [ ] `neatlogs traces export` produces a file; a Share control exists or does not.
- [ ] `identify` with `end_user_metadata` filters by fixture id; `session_custom_fields` without a `session_id` works or does not.
- [ ] `neatlogs usage` shows the span count after the spike, and one story's span count is recorded for the budget.

## 15. What we will not use

- The neatlogs Claude Code plugin to trace our coding sessions: it would share the single project and the 100k cap, and records prompts. Entire covers the coding-agent side.
- Distributed tracing, imports from other tools, Tools & MCPs for Neat Agent, webhooks, secondary clients: not needed.
- Session Replay is experimental ("today one trace maps to one session"): a demo visual if time allows (P2), not a dependency.
- A trained classifier: a separate training job and not available on Free.
