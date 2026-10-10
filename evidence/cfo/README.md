# cfo.ai business model for Storybound

Built 10 Oct 2026 (about 17:20 to 17:50 IST) through the cfoai MCP in workspace "Invisible Technologies" (org 103044).

**Judge-facing read-only link (scenario Main, no password, no expiry, no sign-in needed; opens 5 pages):**
https://app.cfo.ai/s/vGE_ZEwfQtpoxPrg

Link status: the URL returns HTTP 200 and an HTML shell from a plain request. Whether the pages render for an anonymous visitor has not been checked in a private browser window. Do that before submission, and take the screenshots (`evidence/screens/`, name `YYYYMMDD-HHMM-IST-<what>.png`).

## Measured versus assumed (as of 10 Oct 2026)

- **Measured:** nothing. The only measurement-derived inputs are token-count estimates.
- **estimate (token counts, not billing):** text and verification cost per story, $0.0083 ungated (B0) and $0.0162 gated (B1), from sweep-2-p2 (`evidence/reports/20261010-1505-IST-sweep-2-p2.md`). neatlogs holds the measured cost. Gemini thinking tokens may be under-counted, so these may be low.
- **assumed:** sampled verification pays 70% of the gated uplift; picture $0.04; narration $0.002 per page, 8 pages; prices, included stories, overage prices, customers, churn, usage share, hosting $25, other fixed $50, starting cash $2,000, the 60% gross margin bar (ours).
- **published price, unverified for our credits:** neatlogs plan steps; spans per story (150) is a placeholder.
- No accounting actuals. No child data. No Crustdata data.

## Where things are in the model

Pages: Unit economics, Verification and illustration policy, Cash and runway, Assumptions, Evidence and method.
Single place the neatlogs measurement replaces estimates: table **Cost per story inputs** (page Assumptions), column Cost input value, with Unit, Status and Basis columns beside it.
Scenarios: Main Scenario (Verify all, Half illustrations), Growth (overrides new customers and usage share only), Downside (overrides churn and Picture price each only).

## Headline (month 6 = Mar 2027; all estimates and assumptions)

| | Main | Growth | Downside |
| --- | --- | --- | --- |
| Gross margin month 6 | 67.8% | 56.0% | 41.5% |
| Clears the 60% bar | yes | no | no |
| Ending cash Sep 2027 | $8,334 | $11,233 | $4,805 |
| Runway | not burning | not burning | not burning |
| Per-story budget that clears the bar | $0.243 | $0.174 | $0.233 |

Policy at month 6 under Main: Verify all with Full (8 pictures) 43.4% no, Half 67.8% yes, Text only 92.1% yes. Sampled verification changes the margin by under half a point. Growth: only Text only clears. Downside: only Text only clears. Full table: `20261010-1745-IST-cfo-readback-main-growth-downside.json`.

## Files here

- `20261010-1745-IST-cfo-readback-main-growth-downside.json`: summary numbers for the three scenarios, the policy matrix, and the checks run.
- `20261010-1745-IST-cfo-inspect-history.json`: the changelog (34 of 42 entries listed; see its note).

## Caveats recorded at build time

- Runway is 0 (not burning) in every scenario because fixed costs are $75 a month and no founder pay, marketing, payment fees or compliance cost is modelled. This is a limitation, not a finding about the business.
- If neatlogs is not covered by credits, Starter ($99 a month) cuts Main's month-6 margin from 67.8% to 56.1%: below the bar.
- Month 6 is hard-coded as Mar 2027 in the formulas of the table Month 6 reference and in the Canvas block; the policy and Evidence pages contain static numbers written on 10 Oct and will go stale when inputs change.
- Classroom at $29 with 100 stories included is the weak point: 57% margin at 60% usage, 42% at 85% usage.
- Overage is computed on average usage per customer, so it is zero in all scenarios and heavy users are not captured.
- Screenshots, the Version history screenshot and the spreadsheet download are not taken yet (UI steps).
