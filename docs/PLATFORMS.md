# Platforms: what we use, what is done, what is waiting

Updated 11 Oct 2026 (IST). Times are IST. Evidence paths are relative to the repo root. Nothing here contains a key. How each of the three required tools was used is in [TOOLS.md](TOOLS.md); this page is the state of each platform.

## neatlogs (observability), required
| | |
| --- | --- |
| Status | Working. SDK 1.4.26; project `482c3038-22f9-49e6-8938-e816ce252f75`; workflows `create-storybook` and `make-video`; org plan `legacy_unmetered` (read through the CLI) |
| Used for | One trace per story and per video; one GUARDRAIL span per verdict; 7 detections; trace readback and export; triage review; measured cost |
| Evidence | `evidence/traces/`, `evidence/neatlogs/` (triage cards and review, trace costs, measured-vs-estimated cost), `evidence/setup/` |
| CLI | `neatlogs-cli` 0.2.0 signed in by device login with **read-only** scopes (observability, evaluation, configuration, sharing, billing) |
| Not done | Creating human evaluations, alerts, guest links and managed-prompt labels needs write access: dashboard steps for the builder |
| Watch out | The `.mcp.json` server needs `NEATLOGS_API_KEY` in the process environment (start Claude Code from `scripts/dev-shell.ps1`); the MCP rate-limits fast polling; `search_traces fields` is not enabled yet; free-plan traces expire after 14 days |

## Entire (coding-agent memory), required
| | |
| --- | --- |
| Status | Enabled, CLI 0.11.4, hooks installed, `commit_linking: always`, checkpoints sync to `origin`; 37 checkpoints; entire-graph 0.4.0 (local); Brain 0.1.0 with ten durable facts |
| Evidence | `evidence/entire/` (graph diffs for HR-001 to HR-004 and HR-006, impact, verify, `why`, Brain brief and status, checkpoint token comparison), `.entire/runners/` |
| Trails | Runners scaffolded (6) and three tailored to this repo. `entire trail create` and `entire review` answer "repository not found (404)": the Entire GitHub App must be installed on `hatif03/storybound` and the repository selected on entire.io (web step) |
| Honest gaps | Work before 15:08 on 10 Oct was done in a session started outside the repo (no checkpoints); checkpoints contain two pasted keys (rotate both) |
| Submission | Needs `https://entire.io/gh/hatif03/storybound/commit/<FULL_SHA>` and a checkpoint id; the repo is private, so judges need access or the repo must be public |

## cfo.ai (business plan), required
| | |
| --- | --- |
| Status | MCP connected and authorised; workspace "Invisible Technologies" (trial ends 24 Oct; credits confirmed by the builder) |
| Model | Plans (Household, Classroom) x verification policy x illustration policy; scenarios Main, Growth, Downside; pages for assumptions, unit economics, policy, cash, evidence |
| Evidence | `evidence/cfo/` (README with the measured-cost change 275839, readbacks, change history, anonymous-render screenshot) |
| Share link | https://app.cfo.ai/s/vGE_ZEwfQtpoxPrg (read-only; checked anonymously 11 Oct) |
| Open | The quiz and video add-ons are not priced in the model; pictures and voice remain assumed list prices; month 6 is hard-coded as March 2027 |

## Vertex AI Gemini (writer, vision, images, speech)
| | |
| --- | --- |
| Status | Working. Project `project-f0b6b4ce-541f-43ff-9f7`, location `global`, Application Default Credentials |
| Models | `gemini-3.7-flash` (writer, vision, quiz maker, video planner), `gemini-3.1-flash-image` with `gemini-2.5-flash-image` fallback (pictures), Cloud TTS `gemini-2.5-flash-tts` voice Kore |
| Learned | Thinking tokens count against `max_output_tokens`; image quota errors (429) are real and handled by retry and fall-back to text; a 40 s text timeout was tried and reverted (HR-005) |

## K2 Horizon (independent judge)
`IFM/K2-Horizon-375B-A23B`, OpenAI-compatible. Different model family from the writer. 24/24 injected faults caught, 0/88 judge calls unverifiable; 6 to 14 s per call, so judge calls run in parallel and the quiz judge runs on every question.

## Hackathon LiteLLM gateway
`https://litellm.vision.aivar.app/v1` with `claude-haiku`, `claude-sonnet-4.6`, `claude-opus-4.6` and Nova models; key in `.env` as `LITELLM_API_KEY`. Used for a judge comparison only (Claude Sonnet and Haiku caught 23/24 faults, 1 to 3 of 88 unverifiable, 1 to 2 s per call); K2 stays the judge. The key was pasted into the session: rotate it.

## HyperFrames (video rendering)
Apache-2.0, pinned 0.8.145, telemetry disabled. Not used: `publish`, `cloud` rendering, `auth` (they send content to HeyGen). GSAP 3.14.2 is vendored under GreenSock's standard licence.

## AWS
Profile `neathack` (us-east-1). Only EC2, Lambda, IAM roles and load balancers; $25 team allowance; no Bedrock, Polly or S3. Not used: the app runs locally.

## Crustdata (market data)
CLI 0.2.19 installed and the MCP connected, **not used**: no market figure from it is in the repository or the cfo.ai model. Raw Crustdata data must never enter the public repo.

## GitHub
`hatif03/storybound`, private. Commits after 12:30 IST on 10 Oct are inside the window. Publishing is a decision for the builder: see [STATUS.md](STATUS.md) (keys in checkpoints, Entire link access).
