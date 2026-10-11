# From hackathon project to product: what it takes, what video would cost

Written Sun 11 Oct 2026 (IST). Every number below comes from the cfo.ai model (workspace "Invisible Technologies", scenario tree under Main) and is an **estimate or an assumption**, labelled as such in the model. Readbacks: [evidence/cfo/20261011-1250-IST-video-ai-scenarios-and-product-plan-readback.json](../evidence/cfo/20261011-1250-IST-video-ai-scenarios-and-product-plan-readback.json) and [20261011-1215-IST-launch-operating-costs-readback.json](../evidence/cfo/20261011-1215-IST-launch-operating-costs-readback.json). Nothing here is legal or financial advice. How cfo.ai was used overall: [TOOLS.md](TOOLS.md), section 3 and 5.

## 1. What the plan already says (10 Oct)
A story costs about $0.20 to make with the agent choosing four pictures (text and verification $0.0199 measured by neatlogs, pictures $0.16, narration $0.016). At the $6.99 Household price (12 stories included) the infrastructure margin at month 6 is **67.2%** (clears the 60% bar we set). Painting every page fails the bar (42.8%); that is why the product setting `pictures: auto` exists.

## 2. If we ever switched to video AI models (scenarios in cfo.ai)
New inputs in the table "Launch operating costs": clips per story, seconds per clip, price per second, retry allowance (1.4 clips made per clip kept) and a clip-check cost (two vision judges, $0.02). The story cost formula now includes the video cost. Four scenarios, each a child of Main:

| Scenario | Video cost per story | Cost per story (Half pictures) | Gross margin at month 6 | Add-on price that keeps a 60% margin on the video alone |
| --- | --- | --- | --- | --- |
| Main: deterministic motion (today) | $0 | $0.20 | **67.2%** | n/a |
| 3 Lite clips of 4 s ($0.05 per second) | $0.90 | $1.10 | **-70.0%** | $2.25 per story |
| A clip on every page, Fast ($0.10 per second) | $4.64 | $4.84 | -640% | $11.60 per story |
| 3 standard clips of 8 s ($0.40 per second) | $13.50 | $13.70 | -1,990% | $33.75 per story |
| A 3-minute animated story, 45 Lite clips | $13.50 | $13.70 | -1,990% | $33.75 per story |

Reading it: at a $6.99 household price **no video scenario survives**, not even three of the cheapest clips; video would have to be a **separate, priced add-on** (about $2.25 per story for three Lite clips) or a premium tier. This agrees with the decision to keep motion deterministic. Prices are Gemini API list prices (the Vertex bill was not read), and a clip must also pass the clip oath ([HR-009](../evidence/hardening/HR-009.md): the first Veo clip was rejected, so the retry allowance of 1.4 may be low).

## 3. What a real product needs (assumed numbers, new page "Launch plan" in cfo.ai)
| Item | Assumed |
| --- | --- |
| Operating cost per month: one founder $4,000, part-time human safety reviewer $1,000, legal retainer $500, marketing $1,500, insurance $150, tools $150 | **$7,300** |
| One-time: child-privacy legal setup $8,000, impact assessment $3,000, security review $4,000, accessibility audit $2,500, company and trademark $1,500, test devices and a testing panel $2,500, human red-team of the safety screen $2,000 (all placeholders) | **$23,500** |
| Contribution per Household customer per month (price after 15% payment and app-store fees, minus the story cost, support and safety review) | **$2.93** |
| Households needed to cover the operating cost | **about 2,490** |
| Runway if $100,000 is raised, the one-time costs paid and no revenue | **10.5 months** |
| Household price that breaks even at 500 households | **$20.72 per month** |

Reading it: the infrastructure margin is healthy, **the business is not**, because the real costs of a children's product are people, law and trust, not model calls. At $6.99 it needs about 2,500 paying households; at 500 households the price would have to be about $20. The levers, in the order we would pull them: schools and libraries (the Classroom plan: one buyer, many children); a higher family price with a clear safety promise (the receipt is the thing a parent pays for); cheaper human review (the agent already routes only flagged stories to a person); and funding of about $100k to reach evidence of demand. The model's 10 Oct cash table (fixed costs $75 a month, "not burning") is a hackathon-scale view and is kept separate from this one on purpose.

## 4. What turns the prototype into a product (checklist; each item needs a person)
**Law and trust (ask a lawyer, do not rely on this list).** Children's privacy law applies from the first user: COPPA in the US (under 13), GDPR and the UK Age-Appropriate Design Code in Europe and the UK, and India's Digital Personal Data Protection Act (verifiable parental consent for children, and limits on tracking and targeted advertising); app-store rules for children's categories (Apple Kids, Google Play Families); the model and cloud providers' terms for apps used by children (Gemini, the Claude and Nova models behind the gateway, K2 and Veo): **check each one's terms and data retention before a real child's drawing is sent to it**; a parental-consent flow, a privacy policy a parent can read, and a data-deletion path (Forget exists and is tested).
**Safety.** A human red-team of the safety screen with many drawings; a policy for drawings that express fear or sadness (open); a way for a parent to report a story; a human on call for flagged stories; the receipt and the ledger as the audit trail.
**Product.** Accounts for parents only (children never log in); a paid plan and a free trial; offline or flaky-network behaviour; a real iPad, pencil and Safari test; ages 4 and 8 and more languages; a place to keep stories (today nothing is stored beyond Forget-able files).
**Operations.** Monitoring that tells someone (alerts exist, no delivery channel yet); a cost cap per household per day; a status page; backups; incident response.
**Evidence we already have that a buyer cares about:** the per-promise receipt, 0 of 28 stories shipped with a broken promise under the gate against 27 of 28 without, a frozen regression set, holdout results, and the cost per story measured by neatlogs.

## 5. What would change these numbers (the next measurements)
1. Read the real Google Cloud bill for pictures and voice (neatlogs prices text only).
2. Run a paid pilot with a school or a library (Classroom plan) and count stories per child per month.
3. Replace the placeholder legal and compliance lines with quotes.
4. Price the quiz and the read-along movie as add-ons in the same way as video.
