# The hackathon credits and how the work is split across providers

Updated Sun 11 Oct 2026. Measurements: [HR-012](../evidence/hardening/HR-012.md). Nothing here contains a key.

## What we have
| Provider | What it gives | Limit we know | Used for |
| --- | --- | --- | --- |
| Vertex AI (Google) | Gemini 3.7 Flash (text, vision), Gemini image and speech models, Veo | project credits (amount not read); per-minute quotas on images | writer, repairer, oath author, character card, safety screen, pictures, narration |
| K2 Horizon (IFM) | one large reasoning model, OpenAI-compatible | not priced here | the independent judge (a different family from the writer) |
| Hackathon LiteLLM gateway | Claude Haiku 4.5, Sonnet 4.6, Opus 4.6; Nova Micro, Lite, Pro, 2 Lite (no video model) | **$20 over 30 days, 60 requests a minute**; $1.79 spent after today's runs (read from the gateway's key info, 11 Oct) | planner, quiz maker, the "no words in the picture" check, evaluation runs |
| neatlogs, Entire, cfo.ai | tracing, coding-agent memory, financial model | trial and credits as confirmed by the builder | see [TOOLS.md](TOOLS.md) |

## What the data said (11 Oct)
Gemini carried almost everything: 3,478 calls and all of the $4.59 neatlogs measured. Gateway prices (per million tokens in / out, from `/model/info`): Haiku 1.1 / 5.5, Sonnet 3.3 / 16.5, Opus 5.5 / 27.5, Nova Micro 0.035 / 0.14, Nova Lite 0.06 / 0.24, Nova Pro 0.8 / 3.2, Nova 2 Lite 0.33 / 2.75, against Gemini 3.7 Flash at 0.50 / 3.00. **Claude is dearer per token than Gemini Flash**; only Nova is cheaper. So moving work to the gateway does not save money; it spreads load (Vertex's per-minute quota was the cause of two failed jobs, HR-007) and, more important, makes the checks independent of the writer.

## The split we kept, and the ones we rejected
| Role | Model | Why |
| --- | --- | --- |
| Page writer, repairer | Gemini 3.7 Flash | A Claude Haiku writer made the gate repair 4.7 times a story and 3 of 10 stories shipped a break (against 2.1 and 0) |
| Oath author | Gemini | Haiku wrote stricter lesson promises: more repairs |
| Character card (reads the child's drawing) | Gemini | Haiku read a drawn carrot as an ice-cream cone and every picture then failed its check |
| Safety screen | Gemini | Haiku matched 23 of 26 fixtures against 25 of 26, refusing drawings with a caption that should be sanitised |
| Story planner | **Nova 2 Lite** (gateway) | JSON of ten fields, cheap, no loss seen |
| Quiz maker and repairer | **Claude Haiku** (gateway) | text only, checked by six promises and a judge anyway; no loss seen at ten stories |
| "No words in the picture" check | **Claude Haiku** (gateway) | an objective question; the checker is now a different family from the painter; 5 of 5 pictures passed in the live run |
| Text judge | K2 (unchanged) | 40 of 40 ground-truth cells; agrees with Claude Sonnet on 65 of 72 verdicts |
| Pictures, narration | Gemini image and speech | no gateway equivalent |

Set `STORYBOUND_ROUTES=` (empty) to turn the split off; a role falls back to Gemini when no gateway key is present. The receipt and the ledger row record the routes used.

## Where the credits are better spent: evaluation
Serving a story costs about two cents, so the $20 gateway budget cannot be used up by the product. Stronger models earn their cost on **checking our checks**: the cross-family judge agreement run (three Claude models against K2 on 72 promise verdicts, about $1), the safety-screen ablation, the routing experiments. Next uses, in order: have Claude Opus label the 20 verdicts of the neatlogs human-review draft first (a model-to-model number, clearly not a human one) so the human only has to settle disagreements; a Sonnet second opinion on every safety-critical verdict in a nightly sweep; a Sonnet re-read of the receipt text for plain language at age 6.

## Rules we keep
Keys only in `.env`; no child's drawing goes to any provider except in a fixture test, and a real drawing only with a parent's consent and the provider's terms read (CLAUDE.md rule 3; see [BUSINESS.md](BUSINESS.md) section 4). The gateway has a request limit of 60 a minute, so sweeps use three workers.
