# Storybound — the pitch

> **Update 10 Oct:** the model stack is Google Vertex AI (Gemini) plus K2 Horizon as an independent judge; AWS has no Bedrock or Polly in this account (hosting only, $25 cap). See [plan.md section 0](plan.md#0-decisions-of-10-october). Wherever this file says Bedrock, Polly, Nova or Titan, read Vertex, Gemini TTS and Gemini image.

Written 9 October 2026. Companion to [plan.md](plan.md). Everything in square brackets, like `[k of n]`, is a number that does **not exist yet**. It gets filled from `evidence/ledger.jsonl` after the sweeps and never before. A pitch that quotes a number we did not measure loses the one thing the hackathon is judging: evidence.

## 1. Why the two source projects won

Both took part in Datadog's challenge at the "AI Partner Catalyst" hackathon on Devpost. Storytopia's Lighthouse placed **second**, Sworn's Agentic Contract Framework **third**. I read both pitches in full. What they share and what each did well:

| Pattern | Lighthouse (Storytopia) | Agentic Contract Framework (Sworn) | What Storybound takes |
| --- | --- | --- | --- |
| **A question a judge feels** | "Traditional metrics told us the app was 'healthy', but couldn't answer: are the agents always producing high-quality *and safe* outputs?" The gap between *up* and *good* | "As we rely on agents for healthcare, finance and learning, we need to verify their output against domain knowledge, not only infrastructure" | One sentence that names the gap: *an agent that scores itself after the child has already seen the page is not trustworthy* |
| **One memorable model** | Five named signals (creative intent, inappropriate content, lesson alignment, visual consistency, narration status) | **"A contract is a test suite and a commitment is a test case."** Everything else fits that picture. The author is proud of the data model, not the demo | The **oath**: a promise list written before the story, checked page by page |
| **Domain, not generic metrics** | Child safety and lesson alignment, not just latency and tokens | Pedagogy: Socratic questioning, hint frequency, pacing | Children's stories: name in every scene, one correct choice, lesson concept present, no text from the drawing obeyed |
| **A real thing, running** | A hosted app with real kids and parents; "genuinely enjoy creating" | A hosted tutor (Morph) and a pip-installable library (Sworn) built to prove it | A working agent with a child-facing page and a receipt, plus a repo anyone can clone and run |
| **Numbers and a table** | Seven monitors in a table: threshold, purpose, impact | Six detection rules with explicit pass-rate thresholds (70% critical, 80% warning) | A before/after table with counts, and a commitment table |
| **A story of being wrong that produced the insight** | Instrumenting where to attach evaluations was hard; they taught themselves | The agent never closed simulations because the contract did not mention it, which gave "contract coverage". The "confessions" idea failed because agents defend themselves ("a delusional criminal at a lie-detection test"), which gave the *independent verifier* | A real hardening record: a failure we found, the commitment it added, the numbers before and after |
| **Mapped to the sponsor's checklist** | Dashboard, monitors, cases with context, traffic generator, public dashboard link | A **"Key Deliverables and Where to Find Them"** list at the top that points to each required artefact by path | `EVIDENCE.md` generated from a ledger, and a linter that checks the rules the hackathon states |
| **Visual proof** | Six annotated screenshots and a public dashboard | Screenshots of flow, gap, dashboard, alert, plus a video | Trace screenshots, the receipt, the cfo.ai page |
| **Closed the loop** | "Turns observability from passive monitoring into an **active control layer**" (in alerts and cases) | "Finding gaps … turns a linear process into a **cyclical** one" (but listed as *next*) | The loop is **inside the run**: the failure is repaired before shipping, and across runs: trace → fix → proof |
| **Honest about cost and limits** | Mobile not yet optimized; says so | A whole section on "the cost of verifying", sampling and prompt caching | A cost-of-gating number and the cfo.ai decision it feeds |
| **Voice** | Plain, warm, specific | Personal, candid, quotable | Same: first person, concrete, no jargon without a picture |

**What was left on the table** (this is our opening): neither closed the loop *during* the run. Lighthouse's scores arrived after the child had the page; Sworn's verification ran once at the end and listed in-loop control and "finding gaps" as future work. Neither measured whether verification *changes outcomes*. Storybound's claim is exactly that, with numbers.

**What the judges here care about** (from the hackathon page): the agent (30%), neatlogs/Entire/cfo.ai (25%), a ≤ 3-minute video that covers each tool on architecture, implementation, runtime, reasoning and result (20%), building in public (15%), usefulness and originality (10%). The winners' habits above map onto that rubric almost line for line.

## 2. The pitch in one breath

> **Storybound is a storybook agent that keeps its promises.** A child draws a picture; the agent writes an *oath* for that drawing and lesson, checks every page against it **before the child sees it**, rewrites the pages that break it, and gives the parent a receipt. Observe-only, the same oath was broken in **[k of n]** stories. Gated, in **[k of n]**.

Short forms, pick by room:

- **Tagline:** *A story agent you can leave alone with a child's drawing.*
- **Alternates:** *Stories that keep their promises.* · *Verified before it's read.* · *The oath comes first.*
- **Ten-second hook (video):** "A child draws a bunny. By page five the bunny has lost its name — and the story is about to teach the wrong lesson. Storybound catches it before the child ever turns the page."
- **Tweet-length (≤ 280):** "Storybound turns a child's drawing into an 8-page story — and writes an oath first: name on every page, one right answer, the lesson, nothing from the drawing's caption. Every page is checked before it's shown. Break it → rewrite. #neatHack"

## 3. The story (the long version)

### The problem

A story generator can fail silently in ways that matter to a six-year-old. The hero's name vanishes on page five. Both answers teach the same lesson. The correct answer is always the first button, so a child wins by tapping it. A word written *on the drawing* ("Kill fish") reaches the story. Server metrics are green the whole time. And the checks we have for this kind of failure run after the content exists, so the child has already seen it.

### The insight

Two ideas existed, and nobody had joined them. **Storytopia** showed what to measure for a children's story: lesson alignment, character consistency, safety, narration. **Sworn** showed how to be accountable for an agent: write what it owes *before* it runs, give each promise its own verifier, and let a verifier with a different incentive from the writer decide. Put them in the loop instead of after it, and a failed check stops being an alert and becomes a decision: repair, or stop.

### What it does

1. **A drawing comes in.** An independent safety screen reads the pixels *and* any words in the drawing. Visual danger → a calm refusal, with the trace. Words only → the story ignores them, and says so. If the screen itself breaks, it refuses.
2. **The oath is written.** A fixed core, plus promises specific to this lesson and this character. The model can add promises but never remove or relax one. The oath is hashed before a word of story exists.
3. **The story is built page by page.** Each page is checked against the oath: first with cheap deterministic checks, then, on a sample, a judge from a different model family that must *quote* the line it relies on. A page that breaks a promise is rewritten with only the failed verdict as context. Two attempts, then the failure is recorded in the open.
4. **Pictures and narration** are tools that can fail and recover, and the failure is a promise too: retry, then degrade visibly, never skip silently.
5. **A receipt ships with the story.** "14 promises checked. 2 pages rewritten. All kept." For parents: plain language. For judges: the same object is the evidence.

### What is new

- **Verification inside the run**, per page, with repair, not a score afterwards.
- **An oath that can only get stricter**, written from the lesson and the drawing.
- **An independent, quote-checked judge**, because a judge that grades itself, or a judge that invents its reasons, is not a judge.
- **Measured, not claimed:** an observe-only arm against a gated arm, same oath, same fixtures, **[n]** runs each. Shipped-violation rate: **[x]** against **[y]**.
- **The drawing as an attack surface**, tested with a real fixture.
- **The receipt**: verification as something a parent can read.
- **A hardening loop** that turns every real failure into a regression fixture, with the Entire checkpoint that made the fix.

### How it is built

LangGraph orchestrates a state machine with bounded repair loops. Gemini on Google Vertex AI writes, sees and paints; Gemini TTS narrates; K2 Horizon, a different model family, judges. FastAPI serves it; a small storybook page shows it. Every verdict is a neatlogs guardrail span, so the trace is the proof.

## 4. The three tools, as the judges will hear them

Each gets the five points the hackathon asks for: architecture, implementation, runtime, reasoning, result.

### neatlogs: the story agent's flight recorder, and how we found our bugs

- **Architecture:** LangGraph handler for nodes and model calls, decorators for tools, one **guardrail span per promise**, one observer module.
- **Implementation:** each verdict sets `neatlogs.guardrail.passed`, a status-word output and eval attributes; prompts are managed versions.
- **Runtime:** one trace shows scene 5 go red on `character_named_in_scene`, the repair spans, the green re-check; input tokens flat from scene 2 to scene 8; the detection that fired.
- **Reasoning:** Investigate / MCP named the cause of **[failure]**; detections key off the oath, not off generic latency.
- **Result:** shipped-violation rate **[x] → [y]**; cost of gating **[+$z, +s seconds]**.

### Entire: the coding agent's memory, so the fix has a reason

- **Architecture:** Claude Code session → hooks → checkpoint linked to the commit; entire-graph over the repo.
- **Implementation:** `commit_linking: always`; the `Entire-Checkpoint` trailer; the trace ids in the commit message.
- **Runtime:** the fix commit's checkpoint with prompt, transcript, files and tokens.
- **Reasoning:** `entire why` on the changed prompt shows *the session that changed it because that trace failed*.
- **Result:** `entire graph diff`: the added verifier and the changed prompt builder, `graph verify` green after.

### cfo.ai: the business is a model with a measured input

- **Architecture:** Plan and Verification-policy dimensions; Main and Growth scenarios.
- **Implementation:** Ari via MCP; the cost input replaced by a neatlogs measurement (Version history shows the edit).
- **Runtime:** household and classroom plans side by side on customers, revenue, infra and inference, gross profit, gross margin and runway.
- **Reasoning:** the model chose the verification policy and the per-story budget; they are fields in the oath config, set in a named commit.
- **Result:** gross margin **[x%]** on Main, **[y%]** on Growth; runway **[N months / more than 12]**; "cost per story **[$c]**, measured from neatlogs on **[date]**".

## 5. The business, in four lines

Parents and teachers want a story from a child's drawing and cannot read every page first. Household plan **[price]**, classroom plan **[price]**, with a per-story overage. Images dominate the cost of a story; verification is the second lever, which is why the model, not a hunch, sets the sampling rate. The unit economics are on a shared cfo.ai page: **[margin]**, **[runway]**.

## 6. The three-minute video: script with narration

Target ~430 spoken words (about 2.5 words a second). Recorded Sunday night from the frozen path. Each tool section carries the five points. The times follow [plan.md §12](plan.md#12-the-three-minute-demo).

| Time | On screen | Narration |
| --- | --- | --- |
| 0:00–0:15 | The bunny drawing, then the evil-cat drawing. Cat: calm refusal and its trace | "A child draws a bunny. Storybound turns it into an eight-page story, and before it writes a word, it writes an oath. A drawing with a knife? It refuses, calmly, and the trace shows why." |
| 0:15–1:05 | The graph slide, then a live run for "sharing". The oath list. Scene 5 turns red; repair; green. Then the receipt. Then the "Kill fish" drawing: caption ignored, noted | "The oath is a promise list, written first and hashed: the hero's name on every page, one right answer, the lesson, nothing from the drawing's words. Every page is checked before it's shown. Here, page five loses the hero's name. The check fails, the page is rewritten with only that failure as context, and it passes. The parent's receipt says: one page rewritten, all promises kept. And this fish's caption said 'Kill fish'. The story ignored it, and says so." |
| 1:05–1:45 | neatlogs: trace tree; guardrail spans; token chart; detection; B0 vs B1 table; Investigate or MCP | "Architecture: neatlogs records the graph, the tools, and one guardrail span per promise. Here is that red page and its repair. Input tokens stay flat from scene two to eight. This detection fired on it. Investigate named the cause, and the fix is one commit. Result: observe-only, the oath was broken in **[k of n]** stories. Gated, **[k of n]**. Gating costs **[$z]** and **[s]** seconds." |
| 1:45–2:15 | Entire: checkpoint of the fix commit; `entire why`; `graph diff`; `graph verify` | "Entire recorded how the coding agent made the fix. This checkpoint is linked to the commit, with the prompt, the session and the tokens. Asking why this prompt exists returns the session that changed it because that trace failed. The graph diff shows the verifier added and the prompt builder changed, and the tests are green." |
| 2:15–2:45 | cfo.ai: shared page; Version history; Main vs Growth; the sampling-rate and budget decision | "cfo.ai models the business. Cost per story is **[$c]**, measured from neatlogs, and Version history shows that edit. Household and classroom plans, Main and Growth: margin **[x]**, **[y]**, runway **[N]** months. The model chose the verification policy and the per-story budget, and those are fields in the oath config." |
| 2:45–3:00 | The receipt, repo URL, `#neatHack` | "Storybound: a story agent that keeps its promises, and can prove it. The repo, the traces, the checkpoints and the model are linked below." |

Rules for the recording: no scrolling through logs; one cut per segment; captions on every number; the three tools each get a visible label with the five words (architecture, implementation, runtime, reasoning, result) so a judge scoring the FAQ line can tick it; export at ≤ 3:00 and verify with the linter.

## 7. Building in public: five posts, each tied to an artefact

Each post shows something we actually ran. Replace brackets only with ledger numbers. Include `#neatHack`. Under 280 characters.

1. **Saturday, after kickoff (the idea):** "Building Storybound for #neatHack: a storybook agent that writes an *oath* before the story and checks every page against it before a child sees it. Tools: @neatlogs, Entire, cfo.ai. Repo: [url]" + the graph image.
2. **Saturday night (first red trace):** "Page 5 lost the hero's name. The check failed, the page was rewritten, the check passed. That's one trace. The oath caught it before the child could. #neatHack" + the trace screenshot.
3. **Sunday (the numbers):** "Same oath, same drawings, [n] runs. Observe-only: broken in [k]. Gated: broken in [k]. Cost of gating: +[$]/story. #neatHack" + the chart.
4. **Sunday night (Entire and cfo.ai):** "Why does this prompt exist? `entire why` answers with the session that changed it because a trace failed. And the cfo.ai page prices it: [margin], [runway]. #neatHack" + the diff and the page.
5. **Monday (submission):** the quote post of the official neatlogs post: team (solo), name, repo, demo, and the one-line pitch.

Never post a number we have not measured. Never post a child's real drawing.

## 8. The submission post (X, Monday 12 October, 19:00–23:55 IST)

Quote-post the official neatlogs submission post with: team (solo, your name), project (Storybound), the public repo, the demo video, and one sentence: "A story agent that writes its oath first, checks every page before the child sees it, and ships a receipt: observe-only broke the oath in [k of n] stories, gated in [k of n]." Submit by 20:00 IST. Opening the draft is not submitting.

## 9. The README opening (the Devpost equivalent)

The hackathon submits on X plus a repo, so the README is the long-form page, and it should read like the winners': a short summary, a **"Key deliverables and where to find them"** list that maps each hackathon requirement to a path or link (this is Sworn's best habit), then Inspiration, What it does, How it's built, Challenges, What's next. The deliverables list is generated from `EVIDENCE.md`. Skeleton:

```text
# Storybound — a story agent that keeps its promises
<one-breath pitch>   <receipt screenshot>

## Key deliverables and where to find them
Agent improved (before/after, with numbers) ......... EVIDENCE.md §1
neatlogs traces ..................................... EVIDENCE.md §2–3, evidence/traces/
Recovery run (action failed, what next) ............. EVIDENCE.md §2
Entire checkpoints and entire-graph output .......... EVIDENCE.md §7, evidence/entire/
cfo.ai business plan (pricing, costs, revenue, runway) EVIDENCE.md §8 and the shared page
Public posts (#neatHack) ............................ evidence/posts.md
Public repo, commits in the window .................. linter: window check
Demo video .......................................... <url>
Design lineage: Storytopia (Lighthouse) and Sworn (ACF), both MIT, both Datadog-challenge winners
```

## 10. The questions judges will ask, and the honest answers

| Question | Answer |
| --- | --- |
| "Isn't this just Storytopia plus Sworn?" | They are the lineage and we say so. Neither gated a run. Storytopia scored after the child saw the page; Sworn verified once at the end. The new thing is verification *inside* the run, with repair, and a measurement of whether it changes outcomes ([k of n] vs [k of n]) |
| "Who judges the judge?" | The judge is a different model family, must quote the text it relies on (code checks the quote), and we measure agreement with human labels on a sample: **[x%]** [if built]. Where a deterministic check exists, it decides |
| "What did verification cost?" | **[+$z] and [+s] seconds per story**, measured by neatlogs, and cfo.ai's margin under each policy. That is why sampling is a number from the model, not a constant |
| "What if the verifier is wrong?" | Safety fails closed. Quality fails open *and* is flagged in the receipt, so a story is never presented as checked when it wasn't |
| "Can the model write itself an easy oath?" | No. It can add promises, never remove or relax the core. The oath is hashed before any story text exists, and the hash is on the trace |
| "Did you stage the failure?" | No. The baseline is Storytopia's own pipeline shape with the same oath, run **[n]** times. If it was clean on a promise, we say so [and where it was not] |
| "Where did the code come from?" | Written this weekend. The sample drawings and lesson data come from Storytopia with the organizers' approval; the Sworn logic is re-implemented. The git history is dated inside the window |
| "Is a child's data safe?" | No accounts, no stored drawings beyond fixtures, PII redaction on, no real child's drawing in any trace or post |
| "Does the business work?" | **[margin / runway]**, with measured cost and clearly labelled assumptions; image cost is the main lever |
| "What would you do next?" | The adaptive path (the child's answers shape later pages), more lessons, and publishing the oath engine as a library |

## 11. Claims allowed only with evidence

| Claim | Needs |
| --- | --- |
| "Gating cut shipped violations from [x] to [y]" | Ledger rows for both arms, same fixtures and seeds; counts shown |
| "Context stays flat" | Input tokens by scene index from neatlogs LLM spans |
| "The judge agrees with humans [x%]" | The labelled sample exported from neatlogs evals |
| "Cost per story is $c" | neatlogs analytics figure with the date; otherwise say "derived" |
| "Refused unsafe drawings [k of k]; no benign drawing refused" | Ledger rows for each fixture |
| "Ignores words in the drawing" | The "Kill fish" fixture, with the receipt line |
| "Built this weekend" | The linter's window check |

## 12. Voice

First person singular ("I"): we are one builder. Plain words. Concrete before abstract (the bunny before the architecture). One picture per idea. Say the failure out loud; both source pitches were strongest where the author admitted being wrong. Never call it "revolutionary". Never say "AI-powered".
