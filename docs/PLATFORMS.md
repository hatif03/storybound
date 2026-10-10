# Platforms: what we use, what is done, what is waiting

Updated at the end of every milestone. Times are IST. Evidence paths are relative to the repo root. Nothing here contains a key.

## neatlogs (observability)

| | |
| --- | --- |
| Status | Working. SDK 1.4.26 in `.venv`; project `482c3038-22f9-49e6-8938-e816ce252f75`; workflow `create-storybook` |
| Used for | One trace per story; model calls via `neatlogs.wrap`; one GUARDRAIL span per verdict; readback through the MCP server to export traces into the repo |
| Evidence | `evidence/setup/` (doctor local and probe, MCP whoami); `evidence/spikes/` (spike outputs with trace ids); `evidence/traces/` (readbacks) |
| Waiting on you | `neatlogs auth login` (OAuth) if we want the CLI analytics and alert commands; the five detections are created through the MCP `create_detection` tool in M3 |

Log:
- 10 Oct 12:55 Four spike traces sent and read back through the MCP server (`scripts/neatlogs_mcp.py`): Gemini text (`e16a18b5dbcb9cbcac0bd5371a8230f4`, 1 LLM span, 45 tokens, $0.00013), Gemini vision (`4c7153ad26291eb9cd8cedbeaca40f78`, 1173 tokens), K2 judge (`faea948bb4924a0b1ddbe7bd260967e7`, 404 tokens), guardrail (`cc85389a110d01e9407cab538a777ba4`: GUARDRAIL span nested under the WORKFLOW root, input and our output captured).
- Learned: `neatlogs.wrap` on the google-genai client and the OpenAI client both produce proper LLM spans with tokens and cost. Gemini cost counts prompt and answer tokens only, not thinking tokens, so cost is understated (we record our own). K2 cost shows 0 (no price known to neatlogs). The trace id is available mid-run through `neatlogs.inject_trace_context` (the `traceparent` header). The MCP server needs an `initialize` handshake and a session id before `tools/call`.

## Entire (coding-agent memory)

| | |
| --- | --- |
| Status | Enabled, CLI 0.11.4, hooks installed, `commit_linking: always`, checkpoints sync to `origin`. entire-graph 0.4.0 local; Brain installed by hand |
| Used for | Checkpoints of the sessions that build each milestone, the graph for `graph diff` / `graph verify` evidence, `entire why` for hardening records |
| Evidence | `evidence/entire/` (CLI outputs, added as they are produced) |
| Waiting on you | A Claude Code session started inside `D:\storybound` (checkpoints are only recorded for sessions rooted in the repo); `entire login`; Trails access form and the GitHub App import |

Log:
- 10 Oct 12:21 Enabled, graph initialised. 12:37 Brain installed, six project rules stored.
- 10 Oct 12:50 Honest gap: the session that wrote the first milestone commits was started from `D:\neatlogs`, so Entire has no checkpoint for them. Milestones from M2 on should be built from a session started in `D:\storybound`.

## cfo.ai (business plan)

| | |
| --- | --- |
| Status | MCP configured (`.mcp.json`, `.cursor/mcp.json`), OAuth not yet done |
| Used for | The business plan after we have measured cost per story (M7) |
| Waiting on you | Sign in through the MCP prompt in a session rooted in the repo |

## Vertex AI Gemini (writer, vision, images, speech)

| | |
| --- | --- |
| Status | Working. Project `project-f0b6b4ce-541f-43ff-9f7`, location `global`, Application Default Credentials (the signed-in gcloud account) |
| Models | `gemini-3.7-flash` (writer and vision), `gemini-3.1-pro-preview` (reserve), `gemini-3.1-flash-image` and `gemini-2.5-flash-image` (illustration), Cloud TTS `gemini-2.5-flash-tts` voice Kore |
| Evidence | `evidence/spikes/*gemini*` |

Log:
- 10 Oct 12:55 Text and vision spikes pass. Gemini 3 thinking tokens count against `max_output_tokens`, even at `thinking_level=low`: a 200-token cap returned 8 words. The client now adds a 2048-token headroom and refuses to return output that stopped at `MAX_TOKENS`. `thinking_level="minimal"` is rejected by this model; `low` is the floor.
- Claude on Vertex has no quota; Llama and Mistral are not enabled.

## K2 Horizon (independent judge)

| | |
| --- | --- |
| Status | Working. `IFM/K2-Horizon-375B-A23B` at `https://api.ifm.ai/v1` (OpenAI-compatible) |
| Evidence | `evidence/spikes/*k2-judge*` |

Log:
- 10 Oct 12:55 Judge spike passes: structured JSON with a verbatim quote that is a substring of the reviewed text (quote check passes). Latency about 12 s for a 117-token answer, so judge calls run in parallel and are sampled.

## AWS

| | |
| --- | --- |
| Status | Profile `neathack` (us-east-1). Only EC2, Lambda, IAM roles and load balancers; $25 team allowance; Bedrock, Polly and S3 denied |
| Used for | Optional hosting of the demo (M5/M7); not on the critical path |

## Crustdata (market data)

| | |
| --- | --- |
| Status | CLI 0.2.19 installed, MCP configured, not signed in. Raw data must never enter the public repo |
| Waiting on you | An API key or browser sign-in |

## GitHub

| | |
| --- | --- |
| Status | `hatif03/storybound`, private, history pushed at kickoff. Commits after 12:30 IST on 10 Oct are inside the window |
| Waiting on you | Publish before submission (`docs/setup/SETUP.md`) |
