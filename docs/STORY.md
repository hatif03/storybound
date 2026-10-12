# The story: how neatlogs, Entire and cfo.ai changed what we built

For the judges, and for us in a month. Each claim names the file or trace that shows it. Longer detail is in [TOOLS.md](TOOLS.md) (architecture, implementation, runtime, reasoning, result per tool); the product itself is in the [README](../README.md). This page is kept current with every change: `scripts/lint_evidence.py` warns when it, STATUS or the build log fall behind the code.

## The thread in one paragraph
Storybound is an agent that promises things to a child's parent and checks the promises before the child sees a page. The three tools are not decoration around that idea; they are how we found out whether the promises were kept. **neatlogs** made every promise a visible, quoted verdict and told us, from traces we did not write a test for, what was slow, what was wrong and what was merely noise. **Entire** made every change one intent with a checkpoint, found a bug in our own evidence builder, and now gates the next change with rules written from what went wrong. **cfo.ai** turned "what does a story cost" into a decision that went back into the product (the agent now chooses which pages to paint), and then told us, honestly, that video AI would sink the margin and that a real launch needs about 2,500 paying households.

## neatlogs: from traces to fixes
| What neatlogs showed | What we did | Evidence |
| --- | --- | --- |
| One trace per story, one GUARDRAIL span per verdict with the quoted text and the pass/fail | The receipt for parents is built from the same verdicts; a judge can open any story's trace and see which promise held on which page | `evidence/traces/`, [TOOLS.md](TOOLS.md) section 1 |
| Reading level broke on most first-pass pages | Told the writer the limit: pages over the limit fell from 42.9% to 1.8% | [HR-001](../evidence/hardening/HR-001.md), [HR-003](../evidence/hardening/HR-003.md) |
| Its own triage opened three cards, unasked | We verified each before fixing: one confirmed (the 87 s stall), one partly (a "hurts" false positive), one refuted (it read neatlogs's own redaction as app behaviour) | [TRIAGE-REVIEW.md](../evidence/neatlogs/TRIAGE-REVIEW.md), [HR-004](../evidence/hardening/HR-004.md), [HR-005](../evidence/hardening/HR-005.md) |
| Measured cost per story ($0.0199, about 20% above our token estimate) | Replaced the estimate in the cfo.ai model | change 275839, `evidence/neatlogs/20261010-2010-IST-measured-vs-estimated-cost.json` |
| A second pass through traces, detections, alerts and analytics (11 Oct) | Found two detections that had never fired, no alert able to notify anyone, the 87 s stall back in bursts, and an unreported "ignore all" false stop; fixed the stall (hedged retry), the false stop (tiered), and the quiz detection ([HR-011](../evidence/hardening/HR-011.md)); six alert rules exist and need their thresholds retuned | [neatlogs-incident-review.md](research/neatlogs-incident-review.md), `evidence/neatlogs/review-2/` |
| We broke it on purpose (12 Oct): eight configurations and eight injected failures, then read the dashboard like a lab notebook | A stronger writer's parse failure (3 of 10 stories) found in an error span and fixed (10 of 10); a judge outage (0 of 5 shipped) fixed by a judge from another family (5 of 5); three neatlogs incident cards checked: one revealed our own tracing fault (pictures and judge calls outside the story's trace, fixed: 4 of 4 pictures, no fragments), one was our drill, one was refuted by the span | [HR-014](../evidence/hardening/HR-014.md), [HR-015](../evidence/hardening/HR-015.md), [HR-016](../evidence/hardening/HR-016.md), `evidence/neatlogs/review-3/` |
| Two judge-family spans on the same page | The judge bias test and the cross-family agreement check ([HR-008](../evidence/hardening/HR-008.md), [HR-012](../evidence/hardening/HR-012.md)) | `scripts/judge_bias.py`, `scripts/judge_agreement.py` |

What we would say to the neatlogs team: the triage cards and the detections found real things, MCP reads were the fastest way to check a claim, and three gaps cost us time: trace-level regexes cannot see multi-line GUARDRAIL text, error text is missing from `get_trace_context`, and the CLI login lasts only an hour.

## Entire: one intent per checkpoint, and rules for the next change
| What Entire did | Evidence |
| --- | --- |
| 40+ checkpoints, each tied to a commit with one intent; `entire why` and `graph impact` before touching the safety words; graph diffs of the hardening changes | `evidence/entire/` |
| `entire review general` on the PR that documented the history rewrite found five things, one a real bug (the evidence builder printed the latest commit as "First commit") | [PR 1](https://github.com/hatif03/storybound/pull/1), `evidence/entire/20261011-1010-IST-review-general-pr1.txt` |
| `entire review general` on the branch that spread the model work across providers found eight issues, all fixed, including a missing fallback that would have turned a gateway outage into a failed story | `evidence/entire/20261011-1415-IST-review-general-pr2.txt`, [HR-011](../evidence/hardening/HR-011.md) |
| Trails and runners: trails 2 and 3, each backed by a branch and a PR (the cloud runners did not report on those two because "Auto build on push" was off; once it was on, trail 4's review runner reported with no blocking findings); the three tailored runners now say what a prompt or promise change must bring (a bumped prompt version, a hardening record, a regression table) and what a button that deletes a child's work must be (a hold, or undoable) | `.entire/runners/`, [TOOLS.md](TOOLS.md) sections 2 and 5 |
| Brain: durable facts recorded for the next session (Veo only in `us-central1`; gateway budget and routes; small-hands rules; the eval gate; the neatlogs login limit; tuning versus holdout) | `entire brain recall` |
| Honest limits: work before 15:08 on 10 Oct has no checkpoint; two pasted keys reached the checkpoint refs and were scrubbed by an approved history rewrite | [history-rewrite/NOTE.md](../evidence/history-rewrite/NOTE.md) |

## cfo.ai: a business model that talks back to the code
| Question we asked | What the model said | What changed |
| --- | --- | --- |
| Can we paint every page? | No: 42.8% margin at month 6 against our 60% bar; half the pages clears it (67.2%) | The product setting `pictures`, and then `auto`: the agent spends a $0.16 picture budget on the pages that matter ([HR-010](../evidence/hardening/HR-010.md)) |
| Does sampled verification save money? | Under half a point | We kept full verification: safety does not get cheaper |
| What if we used video AI? | Three of the cheapest clips take the margin from 67% to -70%; a clip on every page, -640% | Motion stays deterministic; video, if ever, is a priced add-on (about $2.25 per story for three Lite clips) ([BUSINESS.md](BUSINESS.md)) |
| What would a real launch cost? | About $7,300 a month and $23,500 once (assumed), about 2,500 paying households at $6.99, or a $20.72 price at 500 | A checklist of what a product needs beyond the code ([BUSINESS.md](BUSINESS.md)) |
| Where do the hackathon credits go? | n/a (the gateway holds $20 and a story costs two cents) | A measured split of work across Gemini, K2 and the gateway, and the credits used for evaluation, not as spend for its own sake ([CREDITS.md](CREDITS.md)) |

## The numbers that make the story checkable
- Same writer, 28 drawing-and-lesson pairs: **27 of 28** stories shipped a broken promise ungated or self-reviewing, **0 of 28** gated ([report](../evidence/reports/20261010-1505-IST-sweep-2-p2.md)).
- Held-out drawings the prompts were never tuned on: 10 of 10 shipped with no break ([HR-008](../evidence/hardening/HR-008.md)).
- A frozen set of 16 past failures: 12 resolved under load, all 16 resolved when re-run alone.
- A generated video clip was rejected by the clip oath for redrawing the child's bunny ([HR-009](../evidence/hardening/HR-009.md)); deterministic motion remains the default.
- A first picture at 70 s instead of 278 s ([HR-010](../evidence/hardening/HR-010.md)).

## What did not work, said plainly
A 40 s timeout (reverted); Claude Haiku as the writer (3 of 10 stories shipped a break), as the character-card reader (it saw an ice-cream cone where a child drew a carrot) and as the safety screen (23 of 26 fixtures); trace-level regex detections on multi-line verdicts (never fired); a cfo.ai nested layout (rebuilt); the first regression and reading-pace runs, which overlapped other jobs and are marked as such.
