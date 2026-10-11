# Does Storybound fit the hackathon's problem statement?

> **The problem statement:** "Build an AI agent, or a team of agents, that completes a substantial task from start to finish. Give it a goal, tools and an environment; let each result guide its next action. All projects compete for the same prizes."

**Answer: yes.** Storybound is a team of agents with a goal, tools and an environment; it takes a child's drawing and a lesson all the way to a checked, illustrated, narrated story with a quiz, a movie and a receipt; and its next step is chosen by the result of the last one (accept, repair, regenerate, retry, degrade or stop). Below is the case, point by point, with where to check each claim. The limits come after, because a justification that hides them is not worth much.

## 1. The statement, clause by clause

| Clause | Our answer | Check it |
| --- | --- | --- |
| **A goal** | "Turn this drawing and this lesson into a story the child can read, in which every promise in the oath is kept, and prove it." The goal is stated as a checkable list: the **oath** (22 core promises, lesson-specific ones, grown-up promises, 6 quiz promises). | [DESIGN.md](DESIGN.md), `src/storybound/oath/catalog.py` |
| **Tools** | Drawing vision (Gemini), the page writer (Gemini), an **independent judge** from a different model family (K2) that must quote the text it relies on, a picture model, a text-to-speech service, deterministic checkers (reading level, one right answer, drawing-text screen), a quiz maker, and for video a HyperFrames renderer and a claim resolver that reads evidence files. Each tool call is a span with its input, response, tokens, cost and latency in neatlogs. | [TOOLS.md](TOOLS.md), `src/storybound/clients/`, `evidence/traces/` |
| **An environment** | A LangGraph run with state that survives steps and failures (accepted pages, oath, attempt counters, budget, degradations, tool-call log), a web app a child uses, an HTTP API, a ledger, and the real provider quotas and timeouts. | `src/storybound/pipeline.py`, [API.md](API.md), [WEB.md](WEB.md) |
| **A team of agents** | Distinct roles with their own prompts and context: safety screen, character card, oath author, planner, page writer, judge, quiz maker, and (for video) planner, composer, verifier and repairer. The writer never grades its own work: the judge is another model family, which the experiment below shows matters. | `src/storybound/agents/`, `src/storybound/video/` |
| **Each result guides the next action** | See section 2. | `evidence/ledger.jsonl`, `evidence/reports/` |
| **Substantial task** | See section 3. | `evidence/stories/`, `evidence/runs/` |
| **Start to finish** | A child draws, picks a lesson and reads; nobody edits between the drawing and the finished story. | `web/scripts/e2e-real.mjs`, `evidence/runs/20261011-0910-IST-live-ui-half-pictures-quiz.json` |

## 2. Where a result decides the next step

This is the clause that separates an agent from a script, so here are the decision points, what each one reads, and what it does.

| The result | The agent's next action | Where | Evidence |
| --- | --- | --- | --- |
| A page fails a cheap check (reading level, one right answer, hero named, drawing text) | Rewrite that page now with the failed verdict's expected and actual as context, before the judge looks | `pipeline.n_verify`, `decide()` | Gated arm repaired 1.82 times per story on average (sweep 2) |
| The judge says a page breaks a promise (with a quote that must appear in the page) | **Roll back**: pages written ahead of it are discarded, the page is repaired, review resumes in order | `pipeline.n_settle` | `evidence/reports/20261010-1505-IST-sweep-2-p2.md` |
| A repair does not fix it after two attempts | Quality promise: ship with the break recorded on the receipt. Safety promise: never ship it | `decide()` (`accept_noted`, `stop`) | Receipt, `evidence/hardening/` |
| A critical safety failure | Regenerate once, then stop; the child sees a kind message, not the story | `decide()` (`regen`, `stop`) | Safety eval: unsafe fixture refused, no benign refused |
| The drawing contains written words | Treat them as data: ignore and never repeat them; check that none reached any page | safety node, `no_drawing_text_obedience` | 0 of 8 drawings with text leaked into a shipped story, all three arms |
| The picture or voice service returns an error or 429 | Retry; on a quota error wait four times longer and try once more; then **degrade to text for that page** and say so on the receipt | `clients/retry.py`, `pipeline` media nodes, `Run.degrade()` | Recovery run, trace `94db23729dac6323368749acba4be1cb`; HR-007 |
| The token budget for the story is reached | Turn quality judging off, keep every safety check, record the degradation | `pipeline.n_verify` | Receipt "degradations" list |
| A quiz question fails any quiz promise (quote on the cited page, one right answer, easy words, gentle words, no length tell, judge) | Repair that question twice; **drop** it if it still fails; if fewer than two survive, ship no quiz | `agents/quizmaker.py` | Sweep 7: 104 questions made, 98 shown, 6 dropped |
| The grown-up chose a picture policy (full, half, none) | Paint only the chosen pages and keep words and narration on the rest | `pipeline.picture_pages` | Live run with pages 1, 3, 5, 7 painted |
| Policy **auto** (default since 11 Oct): the planner scored each beat's importance (3 = the hard choice, 2 = meeting the hero or the happy ending, 1 = a quiet step) | The agent spends its picture budget on the highest-scoring pages, paints them most important first, and **stops painting** if the picture service fails twice in a row or the story's budget is gone; pages left unpainted keep words and voice and say why | `pipeline.picture_order`, `Run.painting_should_stop`, receipt `picture_plan` | `tests/test_pipeline.py`, live run in TOOLS.md |
| The movie fails its own video oath (an overclaim, a number not sourced from an evidence file, a length or coverage miss, a render problem) | Repair the failing scene with only that scene as context, re-render, re-verify; **stop** if the failure is not tied to one scene | `video/agent.py`, `video/verify.py` | `evidence/stories/*/video/receipt.json` |

In the experiment these decisions earn their keep. Same writer, same 28 drawing-and-lesson pairs, three arms ([report](../evidence/reports/20261010-1505-IST-sweep-2-p2.md)):

| | B0 ungated | B2 self-review | **B1 gated (the product)** |
| --- | --- | --- | --- |
| Stories shipped with a broken promise | 27/28 | 27/28 | **0/28** |
| Stories with a break on the first pass | 27/28 | 27/28 | 19/28 |
| Repairs per story | 0 | 0.04 | 1.82 |

The gated agent did not start cleaner; it **noticed and fixed** 19 stories' worth of first-pass breaks. The same model asked to review itself fixed almost nothing (0.04 repairs per story). That difference is the point of having a separate checker whose result drives what happens next.

## 3. Substantial, and from start to finish

One real run through the real browser UI (`web/scripts/e2e-real.mjs`, 11 Oct, `--pictures half`) did the following with no human step between the drawing and the end:

1. Read the drawing and screened it for safety.
2. Built a character card from the drawing.
3. Wrote the oath for this drawing and this lesson (plus a grown-up promise typed in the lesson screen).
4. Planned eight beats, then wrote eight pages with review running behind the writer.
5. Checked the whole story against the lesson.
6. Made a four-question quiz and checked every question.
7. Painted the pages the policy chose and narrated all eight.
8. Assembled the receipt: 28 promises checked, 0 pages rewritten, all kept.

A later step builds a read-along movie from the finished story (3:37 and 3:45 renders, all video promises pass). The live script costs about $0.40 plus $0.04 for the movie (text is about $0.02 of a story; pictures and narration are list-price estimates) and takes about 13 minutes including the movie. Two live runs and the 84-run experiment are in `evidence/`.

## 4. What it is not (said plainly)

- **It is a bounded agentic workflow, not an open-ended agent.** The order of stages is a fixed graph (safety, character, oath, write, verify, quiz, media, receipt). The agent chooses *what to do about a result* (accept, repair, roll back, retry, degrade, drop, stop) and, since 11 Oct, *which pages are worth a picture* within a budget; it does not choose *which tool to try next from an open menu*. We chose this on purpose: for children's content a predictable path with open-ended repair inside it is safer and checkable. The video agent's own docstring says it: "a workflow with one agentic loop".
- **Repairs are bounded** (two attempts per node, one regeneration). An exhausted budget ships with the break recorded, except for safety, which never ships broken.
- **The judge is not a human.** Human agreement with the judge was not measured. The judge caught 24 of 24 injected faults and flagged 0 of 8 clean pages, a small test.
- **Samples are small.** 28 stories per arm, one age (6), English, fixture drawings.
- **Pictures and narration costs are list-price assumptions;** neatlogs measures text only.

## 5. Why this is a fair entry against the others

The judges score the agent, the use of neatlogs, Entire and cfo.ai, the demo, building in public, usefulness and evidence. The thing that makes this a good answer to the problem statement is that **every claim of "the result guided the next action" can be checked**: each decision above is a span in the neatlogs trace of the run, each verdict is a GUARDRAIL span with its quote, and the ledger row lists the repairs, degradations and costs. A judge who doubts a line can open the trace named in the evidence column, or run the script in [HANDOFF.md](../HANDOFF.md) and watch it happen.

## 6. If a judge wants a one-minute check

1. Open [EVIDENCE.md](../EVIDENCE.md) and the sweep report above: the three-arm table.
2. Open the recovery trace `94db23729dac6323368749acba4be1cb` in neatlogs, or its export `evidence/traces/20261010-1340-IST-media-run-429-trace.json`: a failed picture call, the retry, the degrade, the receipt line.
3. Open `evidence/stories/bunny-sharing-2/video/receipt.json`: the movie's own checks.
4. `node web/scripts/e2e-quiz-mock.mjs` (free, no models) to see the screens; `?mock=1` in the browser does the same.
