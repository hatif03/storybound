# How Storybound uses cfo.ai (v2)

> **Update 10 Oct:** the model stack is Google Vertex AI (Gemini) plus K2 Horizon as an independent judge; AWS has no Bedrock or Polly in this account (hosting only, $25 cap). See [plan.md section 0](plan.md#0-decisions-of-10-october). Wherever this file says Bedrock, Polly, Nova or Titan, read Vertex, Gemini TTS and Gemini image.

cfo.ai plans the business around the agent. It is not a dependency of the story process: nothing in FastAPI, LangGraph or the oath imports it. Companion to [plan.md](plan.md); see also [neatlog.md](neatlog.md) and [entire.md](entire.md). Written 9 October 2026 against [docs.cfo.ai](https://docs.cfo.ai/llms.txt), [cfo.ai/skill.md](https://cfo.ai/skill.md) and [cfo.ai/pricing](https://cfo.ai/pricing), corrected from [cfo.v1.md](cfo.v1.md). No application code.

The hackathon asks for "a business plan covering pricing, costs, revenue, and runway", shown in the demo, with a clear role for cfo.ai in "planning its business". Its illustrative table is Base 100 customers / $2,000 revenue / $400 infra / $1,600 gross profit / 80% margin against Growth 250 / $5,000 / $850 / $4,150 / 83%. That table is their example of the shape, not numbers to reuse.

## 1. Corrections to v1 (verified against the docs)

| v1 claim | Fact | Source |
| --- | --- | --- |
| Scenario is a dimension (Main, Growth) | **Scenarios are a model-level construct**: a Main plus child branches. Not a Dimension. Remove it from the Dimensions table | [understand-scenarios](https://docs.cfo.ai/scenarios/understand-scenarios.md) |
| Replace `Cost per story` in Main and Growth is unaffected | **A child Scenario stores only the values it overrides and follows later Main edits.** Replacing cost in Main flows into Growth unless Growth overrides it. Override only the drivers that should differ (new customers, churn, stories used) | same |
| A "Verification choice" page with two sampling rates as two columns on Main | A Table Block can compare Scenarios but cannot show two parameter values side by side. Add a **`Verification policy` Dimension** (Verify all, Sampled) used by the cost rows | [formula syntax](https://docs.cfo.ai/formulas/formula-reference/formula-syntax-and-operators.md) |
| "The free trial is enough"; MCP available to us | The MCP server needs an **approved account** ([cfo.ai/llms.txt](https://cfo.ai/llms.txt)). The billing doc also describes a Free plan (one-time AI credit, CSV-only data) whose MCP access is **unverified**; pricing lists MCP under the paid tiers. **Start the 14-day trial today**, so MCP is testable on Saturday morning | [billing](https://docs.cfo.ai/workspace-settings/billing.md) |
| Startup $375/month billed annually | Startup is $500 monthly or $375/month billed annually; Growth $1,500 / $1,125. Trial: 14 days, nothing charged at start, one trial per workspace; **when the trial's AI usage is exhausted a "Start paid plan" button appears and charges the card** | [pricing](https://cfo.ai/pricing), [billing](https://docs.cfo.ai/workspace-settings/billing.md) |
| `inspect_variables` / `inspect_dimensions` as read tools | They appear only in `skill.md`, parameters undocumented. The MCP page lists `inspect_table_blocks`, `inspect_pages`, `inspect_canvas_library`, `inspect_scenarios`, `inspect_integrations`, `inspect_skills`, `inspect_documentation`, `list_orgs`; agent-instructions adds `inspect_dimension_mappings`, `inspect_history`, `validate_code_blocks`, `inspect_reference` | [mcp-server](https://docs.cfo.ai/integrations/mcp-server.md), [agent-instructions](https://docs.cfo.ai/agent-instructions.md) |
| Write tools unspecified | Names verified, parameters not documented: `edit_table_blocks` (tables, Variables, Dimensions and **all formulas**), `edit_pages`, `edit_scenarios`, `edit_canvas_blocks`, `edit_dimension_mappings`, `edit_integrations`, `edit_triggers`. Call shape: one block named for the action, e.g. `{"read":{"target":"Operating Plan"}}`. Formula writes support `dry_run`. Writes hit the live Model. Deleting a used Variable needs `force:true`. Use the exact `Name#hex` references from inspect results | same |
| Skip straight to modelling | The docs say to read `inspect_skills` (list, then the instructions for `build-model`) **before** modelling | agent-instructions |
| "Cursor" | The docs cover Claude Code and Codex; others via the generic "custom connector / MCP server" route. We use Claude Code | [mcp-server](https://docs.cfo.ai/integrations/mcp-server.md) |
| Export "or screenshot" | The only documented export is **Download spreadsheet** (xlsx; one sheet per Table Block plus "Model inputs"; charts and Canvas blocks excluded). PDF, CSV and PNG export are not documented, so screenshots are the visual backup | [share-pages](https://docs.cfo.ai/dashboards/share-pages-and-scenarios.md) |
| "Ari's changelog" | **Version history** (clock icon in the Page header) records every change by Ari or a human with author and time; view as-of, undo, redo, restore. MCP has `inspect_history` | same |
| Cost per story ≈ $0.40 with **one** illustration | Storybound makes **eight** illustrations, one per scene. See §5 | [plan.md §4](plan.md#4-what-storybound-is) |
| neatlogs spans per story ≈ 40 | A gated story is ~**150** spans ([neatlog.md §3](neatlog.md#3-free-plan-limits-and-what-they-force)); to be replaced by a measurement | |
| Household $12, Classroom $49 | Category median list price is $9.99/month and $44.99/year ([RevenueCat 2026](https://www.revenuecat.com/state-of-subscription-apps-2026-education)); $49 per classroom per month (~$20 per student per year for 30) is at the top of the K-12 licence range. See §4 | |
| "70% gross margin" as the bar | AI-native application gross margins are reported around 50–60% (secondary sources). 70% is ours, aggressive, and clearable only with a cheap image model or fewer images. Show 60% as the typical-AI-app reference line | [§6](#6-the-decision-the-model-exists-to-make) |

Verified and kept: sign-in at [cfo.ai/start](https://cfo.ai/start) or [app.cfo.ai/login](https://app.cfo.ai/login) with verification and payment in the browser and never in chat; one workspace; MCP server `cfoai` at `https://api.cfo.ai/mcp`, Streamable HTTP, OAuth, no API key; "an empty model is a valid result"; alternatives go in a Scenario, not Main; sharing a Page by read-only link that **recipients can open without signing in** (optional password); Ari can create and compare Scenarios, review history, and mark values as sourced vs assumed.

## 2. Account and MCP

1. **Today:** open [cfo.ai/start](https://cfo.ai/start) and create the account, one workspace. Per the builder, special credits arrive at kickoff, so apply them before relying on the trial; the 14-day trial stays the fallback. You are the billing owner: watch the usage meter, and do not click "Start paid plan" until the credit terms are known. No passwords, codes or tokens in chat.
2. **Saturday morning:** in a normal interactive Claude Code session (not a headless one; OAuth needs a browser): `claude mcp add --transport http cfoai https://api.cfo.ai/mcp`, then `/mcp`, select `cfoai`, Authenticate. Restart the client if tools do not appear.
3. **Prove it with reads:** `list_orgs` (pass `org_id` if several), then `inspect_skills` (the `build-model` skill), then `inspect_pages`, `inspect_table_blocks`, `inspect_scenarios`, `inspect_history` on the empty model. Configuration without a read is not "connected". Report account access, MCP connection and a working model as three separate milestones.
4. **Rules for writes** ([agent-instructions](https://docs.cfo.ai/agent-instructions.md)): inspect before changing; `dry_run` formula writes first; create the `Growth` Scenario **before** any Growth edits and change Growth only; never put secrets in chat.
5. **Fallbacks:** MCP unavailable or the account is not approved → build in the app, where Ari does the same work (the MCP is a client of the same Model). Or build the numbers in a spreadsheet, attach the xlsx to an Ari chat (up to 5 files, 50 MB each) and ask it to rebuild natively ([import a spreadsheet](https://docs.cfo.ai/getting-started/import-a-spreadsheet-model.md)). Sharing blocked → screenshot plus the "Download spreadsheet" xlsx in `evidence/cfo/`, and say so.

The cfo.ai subscription itself is a planning tool for us, not a cost of goods; it does not appear in the model.

## 3. The decision the model is for

Two questions, both wired back into the agent:

1. **What can we charge a household and a classroom, and what does it cost to serve them?** Cost per story is measured from neatlogs, not guessed.
2. **How much verification can we afford, and what per-story budget should the agent run under?** The agent has two cost knobs: the judge sampling rate on quality commitments ([plan.md §8.3](plan.md#83-verification-mechanics)) and the budget governor's per-story budget ([plan.md §7.6](plan.md#76-budget-governor-p1)). The model's gross margin under "Verify all" versus "Sampled" and under a given image count decides both. The values we ship are the values the model supports, and the commit that sets them is named in the evidence. That is the difference between attaching a spreadsheet and using cfo.ai to plan the business. Safety checks stay at sampling 1.0 regardless: they are not a cost knob.

## 4. Model shape

Time grain: months, twelve forward. Date dimension built in. **No Last close is set, so every period is Forecast.** There are no accounting actuals; every input is an assumption until overwritten from a neatlogs measurement. State this on the page.

**Dimensions:** `Plan` {Household, Classroom}; `Verification policy` {Verify all, Sampled}, used only by the cost rows on page 3; Date (built in). Scenarios are separate: **Main** (baseline) and **Growth** (created from Main via `edit_scenarios` or by asking Ari; never merged back; take a Snapshot before the demo to freeze it).

**Prices (assumptions, the decision).** Household **$9.99/month** (the category median; an annual option near $44.99–59.99 can be a variant). Classroom priced **per classroom**, assumed **$29/month** for ~30 students (~$11.60 per student per year, inside the K-12 licence range of ~$3–20); the $49 of v1 is untested and high. Overage: $0.40 per story household, $0.15 classroom. Included stories: 20 household, 200 classroom. Churn: household 8%/month, classroom 3%/month, **assumptions** (no education churn or CAC benchmark was found; label both).

**Variables** (by Plan unless noted). Mark each input as *measured* or *assumed* in its name or notes.

| Variable | Formula or starting point | Source |
| --- | --- | --- |
| `Starting customers` | Household 40, Classroom 10 | Assumed |
| `New customers` | Main: Household 8, Classroom 1. Growth overrides: Household 20, Classroom 4 | Assumed |
| `Monthly churn` | Household 8%, Classroom 3% | Assumed |
| `Churned customers` | `` `Ending customers`[-1] * `Monthly churn` `` | Formula |
| `Ending customers` | `` `Ending customers`[-1] + `New customers` - `Churned customers` `` (month 1 = Starting customers) | Formula |
| `Price per month` | $9.99 / $29 | Assumed, the decision |
| `Stories included`, `Stories used per customer` | 20 / 200 included; used 60% of included on Main, 75% on Growth (Growth override) | Assumed |
| `Overage price` | $0.40 / $0.15 | Assumed |
| `Subscription revenue` | `` `Ending customers` * `Price per month` `` | Formula |
| `Overage revenue` | `` `Ending customers` * if(`Stories used per customer` > `Stories included`, (`Stories used per customer` - `Stories included`) * `Overage price`, 0) `` | Formula |
| `LLM cost per story` | tokens in × in-price + tokens out × out-price | **Measured** from neatlogs once a sweep exists |
| `Image cost per story` | `Images per story` × `Cost per image` | `Images per story` is a policy (up to 8); `Cost per image` from the Bedrock price of the chosen model |
| `TTS cost per story` | characters per story × `Cost per char` | Measured count, published Polly price |
| `Judge cost per story` (by Verification policy) | the verification uplift; Verify all vs Sampled | **Measured** from the judge spans |
| `Spans per story` | placeholder 150 | **Measured** from a trace |
| `Cost per story` | sum of the four cost rows, by Verification policy | Formula; the measured input to replace |
| `Stories delivered` | `` `Ending customers` * `Stories used per customer` `` | Formula |
| `Inference cost` | `` `Stories delivered` * `Cost per story` `` | Formula |
| `Neatlogs bill` | `if(spans <= 100000, 0, if(spans <= 250000, 99, 99 + ceiling((spans - 250000) / 100000) * 10))` with spans = `Stories delivered` × `Spans per story`. Note Free is a **hard cap** at 100k | Published price + our span count |
| `Hosting`, `Other fixed costs` | $25; small, assumed (domain, misc) | Assumed |
| `Revenue` | Subscription + Overage | Formula |
| `Infra and inference` | `Inference cost + Neatlogs bill + Hosting` | The hackathon's cost line |
| `Gross profit`, `Gross margin` | `Revenue - Infra and inference`; `if(Revenue <> 0, Gross profit / Revenue, 0)` | Formula |
| `Founder draw` | $0 | Assumed |
| `Net cash flow`, `Ending cash` | `Gross profit - Other fixed costs - Founder draw`; `` `Ending cash`[-1] + `Net cash flow` `` (month 1 = starting cash, $2,000) | Formula |
| `Runway months` | `if(Net cash flow < 0, Ending cash / -Net cash flow, 0)` plus a "month cash crosses zero" row. The docs do not define runway, so validate with `dry_run` or ask Ari to reconcile | Formula |

Formula syntax ([reference](https://docs.cfo.ai/formulas/formula-reference/formula-syntax-and-operators.md)): backticks for names with spaces; `X[Plan = "Household"]` lookups; `X[-1]` prior period; `sum(X[Plan in any])` aggregation; `if(...)`, `iferror(...)`. Spreadsheet-style cell values override the row default formula.

**Pages** (each a Table Block Ari can reconcile):

1. **Unit economics.** Plan on rows; Main with a Growth comparison; the six hackathon lines: customers, revenue, infra and inference, gross profit, gross margin, runway. **This is the shared page.** Scenario comparison cannot be combined with a shifted time period; monthly Date columns can still appear alongside.
2. **Twelve-month cash.** Date on columns; ending cash and runway; Main only.
3. **Verification and budget.** `Verification policy` across the columns; cost rows only. The column that clears the margin bar sets `semantic_sampling_rate` for the quality commitments and the per-story budget.

Add a reconciliation row: gross profit equals revenue minus infra and inference; customers roll forward. If totals disagree the model is not done.

## 5. Where the cost numbers come from

**Placeholders** (cited, illustrative, replaced from neatlogs):

- Claude Haiku 5.5 on the first-party API is $0.10 in / $0.50 out per million tokens; Sonnet 5.5 $2 / $10 ([pricing](https://platform.claude.com/docs/en/about-claude/pricing)). **Bedrock prices are separate and were not verified**; Anthropic notes a regional-endpoint premium for some generations. Nova per-million-token rates (Micro $0.035/$0.14, Lite $0.06/$0.24, Pro $0.80/$3.20) are from **secondary** sources.
- Images: Nova Canvas ~$0.04 per standard 1024² image; Titan Image Generator v2 ~$0.01 (AWS confirms one line: 1,000 images × $0.01 for a Titan base model at 1024² standard; the rest is secondary).
- Polly ([verified](https://aws.amazon.com/polly/pricing/)): Standard $4, Neural $16, Generative $30, Long-form $100 per million characters.
- neatlogs ([pricing](https://neatlogs.com)): Free $0 with a 100k-span hard cap; Starter $99/month for 250k then $10 per 100k; Pro $499/month for 1M then $8 per 100k.

**Back-of-envelope, not measured:** an 8-scene story with a Haiku-class writer and judge costs about a cent or two in LLM tokens and roughly $0.04 in sampled judge calls. Eight Canvas images ≈ $0.32; eight Titan images ≈ $0.08. About 3,000 characters of Neural TTS ≈ $0.05. Total ≈ **$0.42 with Canvas, ≈ $0.18 with Titan**. **Images dominate cost.** The levers, in order: image model, image count per story (the governor's "illustrate only the key scenes" mode), then sampling, which is second-order. A household using 12 stories a month at $9.99 therefore lands near ~50% gross margin with Canvas and ~75% with Titan before neatlogs and hosting. Ari does the actual arithmetic; this is only the expectation to check the model against.

**Observability is a real cost line, and a product decision.** At ~150 spans per story, 1,200 stories a month is ~180k spans: over the Free cap, so Starter at $99 (~$0.08 per story, a large share of a $0.18 story). The levers: production `sample_rate` below 1.0 (the hackathon build keeps 1.0), fewer GUARDRAIL spans for sampled-out checks (they are LOG lines, not spans), or the Pro tier. The model carries `Spans per story` precisely so this shows up.

**Replacing placeholders (Sunday, after the sweeps):**

1. `neatlogs analytics kpis|cost|chart` for workflow `create-storybook`: median cost, median and p95 latency, span count, token totals. One benign story and one repaired story, because repairs are part of the product. Note the CLI window limit (30 days).
2. In Claude Code with `cfoai` connected, ask Ari to replace `LLM cost per story`, `Judge cost per story` and `Spans per story` with these figures in **Main**, label them "measured from neatlogs workflow create-storybook on <date>", leave every other variable as an assumption. Remember Growth follows Main unless it overrides.
3. Ask Ari to recompute margin and runway on Main and Growth, and to say whether "Verify all" still clears the margin bar in month 6.
4. Set the oath config (`semantic_sampling_rate`, per-story budget) to the column that clears the bar. That is a commit in the window; the evidence names it.

If Bedrock cost is missing from a span, multiply tokens by the published price for that model id, show the arithmetic in the Ari chat, and label it "derived", not "measured".

## 6. The decision the model exists to make

State a bar explicitly so the decision is auditable: **gross margin ≥ 60% on Main in month 6** (the typical AI-app level) with a stretch line at 70% (ours). Sources for 50–60% AI-app margins are secondary summaries (SaaStr, CloudZero and others); label the bar as ours. The verification choice then reads: the highest policy (most judge coverage on quality commitments, full image verification) that still clears the bar; otherwise the cheapest image model or fewer illustrated scenes. The result is written into `evidence/cfo/` and the oath config in the same commit.

## 7. What the demo shows (30 seconds, five points)

The shared Page is the artefact; the chat is not toured.

1. **Architecture:** the Plan and Verification-policy dimensions and the Main/Growth scenarios.
2. **Implementation:** Ari via MCP built it; Version history open for five seconds showing the cost replaced by a neatlogs measurement.
3. **Runtime:** Main versus Growth side by side on the six lines, with a visible "measured vs assumed" tag on each input.
4. **Reasoning:** the sentence "cost per story is $X, measured from neatlogs workflow `create-storybook` on <date>"; the sampling rate and per-story budget the model supports and the oath field each set.
5. **Result:** gross margin on Main and Growth, and the runway sentence ("cash lasts N months, or more than 12 at $2,000 starting cash").

## 8. What goes into EVIDENCE.md and `evidence/cfo/`

- Workspace name and the shared page URL (open it once in an incognito window); password, if any, sent separately.
- A screenshot of the Page, a Version history screenshot, and the "Download spreadsheet" xlsx.
- The date `Cost per story` was replaced, the neatlogs analytics figure it came from, and the number.
- Main versus Growth for customers, revenue, infra and inference, gross profit, gross margin and runway.
- The sampling rate and per-story budget chosen, and the commit that set them.
- A line: "No accounting actuals. Revenue, churn and prices are assumptions. Inference cost, span count and judge cost are measured." And a pointer to the COPPA/child-privacy compliance cost the model does not include, as a known limitation.

## 9. What we will not do

- Put cfo.ai calls inside the story graph. A child generating a story does not need a forecast.
- Book Crustdata or Dodo Payments into the model for sponsor credit. Dodo can be named as a billing rail; it is not a requirement, and a fake integration is worse than an honest assumption.
- Merge Growth into Main. The comparison is the point.
- Let Ari invent a headcount plan. Founder draw is zero.
- Call the pre-revenue model "forecast actuals".
- Click "Start paid plan" without the billing owner's decision.

## 10. Risks

| Risk | Response |
| --- | --- |
| MCP auth fails, account not approved, Free plan lacks MCP | App UI with Ari, or spreadsheet import. Authenticate in an interactive session; this is a human step |
| Trial AI usage runs out and a paid plan charges the card | Watch the meter; apply the hackathon credits first; decide before clicking |
| Sharing blocked or restricted | Screenshot plus xlsx; say so |
| Growth silently inherits Main edits | Override only the drivers; check the Scenario's overrides before the demo; snapshot Growth |
| Measured cost arrives late | The model is built Saturday night on placeholders; only three inputs change Sunday |
| Bedrock prices unverified | Spike S1 reads the account's actual model list; confirm prices on the AWS page; label "derived" until neatlogs reports cost |
| Free neatlogs cap stops ingestion before the sweep ends | Count spans before each sweep; keep a reserve |
