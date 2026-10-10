# Crustdata: how we use it (and how we do not)

Crustdata is a B2B data platform (companies, people, jobs, social posts, web search and fetch). It is **not** part of the story-generation path and never receives children's data. Its job here is **market evidence for the cfo.ai business plan and the pitch**. Docs: https://docs.crustdata.com/general/introduction · index for agents: https://static-assets.crustdata.com/llms.txt

## Setup status (10 Oct)
| Item | State |
| --- | --- |
| CLI `crustdata` 0.2.19 | installed (`~/.crustdata/bin`); not logged in |
| MCP server `https://install.crustdata.com/mcp` | configured in `.mcp.json` (Claude Code) and `.cursor/mcp.json` (Cursor), OAuth; sign in with `/mcp` |
| API key | **not yet provided**: put it in `.env` as `CRUSTDATA_API_KEY`, or sign in through OAuth |
| Free smoke test | `crustdata account credits --jq .account.credits` or `curl https://api.crustdata.com/account/credits -H "Authorization: Bearer $CRUSTDATA_API_KEY" -H "x-api-version: 2025-11-01"` |

Facts to remember: base URL `https://api.crustdata.com`; every call needs `x-api-version: 2025-11-01`; every response carries `X-Credits-Used`; `/company/identify`, autocomplete, account endpoints and `limit: 0` counts are free; use the CLI's `--dry-run` first. Credits are shared across keys; zero results cost zero.

## What we will use it for (cheapest first)
1. **Competitor and market map for the cfo.ai model.** `/company/search` for education and e-learning companies by country, headcount and funding (about 0.03 credits per result), then `/company/enrich` on 5 to 10 named rivals (2 credits each). Output: assumptions for market size, headcount and funding, cited as "Crustdata, <date>" in cfo.ai. Expect noisy industry tags and hand-curate.
2. **Competitor positioning and pricing.** `/web/enrich/live` on rival pricing pages (1 credit per page) and `/web/search/live` for press and reviews (1 credit); summarise with our own model. Feeds the household and classroom price points.
3. **Hiring signals** (`/job/search`): what children's-education AI companies hire for. Colour for the pitch only.
4. **Classroom-tier lead sampling** (stretch): schools and edtech distributors, weakly covered in a B2B dataset; treat as a sample.
5. **Creator outreach** (skip unless credits are spare): professional-persona search only, a handful of people, human-reviewed.

## Rules
- **Never send children's data or minors' personal data** in any query, filter, URL or MCP prompt.
- **Raw results never enter the public repo** (Crustdata's data-export terms forbid publishing or sharing the Data outside the organisation and require deletion on opt-out). Keep pulls in a local gitignored folder (`data/crustdata/`); commit only our own aggregates with Crustdata cited as the source. If unsure whether an aggregate chart is allowed, ask Crustdata at the hackathon.
- Keep the key in `.env`; use `${env:CRUSTDATA_API_KEY}` in editor configs, never the literal.
- Record each pull in `evidence/cfo/` as a one-line note (query, credits used, date), not the data.
- Honest framing in the video: "Crustdata sized the market for the business plan", not "Crustdata powers the product".
