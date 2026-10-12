# Submission checklist (neatHack, Mon 12 Oct 2026, 19:00 to 23:55 IST)

Written for: the builder, for the day of submission. From the neatlogs team's message of 12 Oct: two steps are required and both are detected automatically; if either is missing the submission is not seen. The first 50 quote-tweets get engagement from the team, so post early (from 19:00).

## The two required steps
1. **Quote-tweet the official @neatlogs launch post on X** (the team shares the link at 7 PM IST on Discord). The quote-tweet must tag **@neatlogs, @EntireHQ and @arithecfo**.
2. **Fill in the submission form** (link shared at 7 PM IST on Discord).

## What the form needs (get these ready before 19:00)
| Item | Where it is | State |
| --- | --- | --- |
| Team name | Yours to choose (solo entry) | decide |
| Project name and description | Drafts below | edit and paste |
| Public GitHub repo with the code | https://github.com/hatif03/storybound (public). The code is on `main` only after PR 4 is merged: **merge PR 4 first** ([the experiments branch](https://github.com/hatif03/storybound/pull/4)) so the repo a judge opens has the final code | **open: merge PR 4** |
| Demo video (about 3:07; the builder approved up to 3:10) | Made: `evidence/demo/storybound-demo-3min.mp4`. Watch: https://storybound-xi.vercel.app/videos/storybound-demo-3min.mp4 or https://github.com/hatif03/storybound/releases/tag/demo-videos (download). For X and the form, upload the file to X or YouTube (unlisted) and use that link; the full tour is at /videos/storybound-full-tour.mp4 | upload |
| Entire checkpoint link | `https://entire.io/gh/hatif03/storybound/commit/<full sha>` (see STATUS item 3), test in a private window | check |
| cfo.ai share link | https://cfo.ai/s/vGE_ZEwfQtpoxPrg (does not show the Launch plan or Video AI pages added later; the Version-history screenshots are in `evidence/cfo/`) | check |
| neatlogs project | traces, incidents, detections, alerts and the human evaluation are in the project; screenshots and exports are in `evidence/` | check |

The brief's bonus: the demo video should clearly explain the problem and how the solution works. The script is built around that (problem, the oath and the receipt, then the incidents neatlogs found and the fixes).

## Draft: project description (paste and edit)
**Short (about 50 words):** Storybound turns a child's drawing into a storybook that teaches a gentle lesson. Before any page reaches a child aged four to eight, an agent checks it against an oath it wrote for that drawing and lesson, rewrites what breaks, and gives the parent a receipt of every promise kept.

**Longer:** A child draws a hero and picks a lesson such as sharing. The agent first writes an oath, a list of checkable promises (safe words, the hero on every page, the lesson shown, reading level, no words painted into pictures). It writes each page, checks the page against every promise, rewrites any page that breaks one, and shows a page only when its words, picture and voice all exist. The parent's receipt lists every promise, every rewrite and anything that could not be kept. neatlogs shows each promise as a traced, quoted verdict and found the incidents we fixed; Entire kept every fix as one checkpoint and its review caught defects in our own fixes; cfo.ai turned the cost of a story into the decision of which pages to paint. Evidence for every claim is in the repo (`EVIDENCE.md`, `docs/STORY.md`).

## Draft: the quote-tweet (about 270 characters before the link; check the count when you paste)
```
Storybound: a storybook agent for kids 4-8. It writes an oath for each drawing, checks every page against it before the child sees it, rewrites what breaks, and ships a receipt. Built with @neatlogs @EntireHQ @arithecfo #neatHack
Video: <link>  Code: github.com/hatif03/storybound
```
Rules: quote-tweet the official launch post (not a new post), keep all three tags, no real child's name or face, no key. After posting, add the URL, time and what it shows to `evidence/posts.md`.

## Answers for the submission form: how we used the tools (copy and paste)
Full page with screenshots, tables and every link: **https://storybound-xi.vercel.app/judges/** (also in the repo at `web/public/judges/index.html`). Dashboard screenshots: [evidence/dashboards/](https://github.com/hatif03/storybound/blob/main/evidence/dashboards/). The same answers are in this file for copy and paste.

### neatlogs: what did you trace, debug or improve?
We traced every story as **one trace**: the oath, each page, each judge call, each picture and voice, with every promise check as its own span holding the quoted words and the verdict. We then used neatlogs to find our own bugs, always trace first, then fix, then compare runs:
- **Reading level** broke on most first-pass pages; telling the writer the limit cut pages over the limit from 42.9% to 1.8% ([HR-001](https://github.com/hatif03/storybound/blob/main/evidence/hardening/HR-001.md), [HR-003](https://github.com/hatif03/storybound/blob/main/evidence/hardening/HR-003.md)).
- **neatlogs's own triage cards** (an 87 s Gemini stall, "hurts" flagged critical, a PII card): one confirmed, one partly, one refuted, each checked before any fix ([TRIAGE-REVIEW](https://github.com/hatif03/storybound/blob/main/evidence/neatlogs/TRIAGE-REVIEW.md), [HR-004](https://github.com/hatif03/storybound/blob/main/evidence/hardening/HR-004.md), [HR-011](https://github.com/hatif03/storybound/blob/main/evidence/hardening/HR-011.md)).
- **Error spans** of a stronger writer showed 3 of 10 stories ending in a page-format error; after a tolerant parser, 10 of 10. **Drills** we ran on purpose showed no story shipping with the judge down (0 of 5); with a judge from another family, 5 of 5 ([HR-014](https://github.com/hatif03/storybound/blob/main/evidence/hardening/HR-014.md), [HR-015](https://github.com/hatif03/storybound/blob/main/evidence/hardening/HR-015.md)).
- **Incident cards** ("repair loop never ends", "latency in illustrate", "K2 returns prose") were checked against their traces: the repair cap holds, one was our own drill, one was refuted by the span, and the first exposed a fault of ours (pictures and judge calls missing from the story's trace: 2 of 4 pictures before, 4 of 4 after). Fixed, with the before and after traces saved ([HR-016](https://github.com/hatif03/storybound/blob/main/evidence/hardening/HR-016.md)).
- **Detections, alerts and evaluations:** a picture-words detection that was blind until the fix then fired on a drill; seven alert rules with email delivery; a human evaluation of single judge verdicts ([neatlogs evidence](https://github.com/hatif03/storybound/blob/main/evidence/neatlogs/), [screenshots](https://github.com/hatif03/storybound/blob/main/evidence/dashboards/neatlogs/)).
- **Measured cost** ($0.0199 per story, about 20% above our estimate) replaced the estimate in the cfo.ai model.

### Entire: how did you use it?
Entire recorded the coding agent that built Storybound (97 checkpoints in 132 commits, 4 trails merged, per its analytics). On Entire: [overview](https://entire.io/gh/hatif03/storybound), [commits and checkpoints](https://entire.io/gh/hatif03/storybound/commits), [trails](https://entire.io/gh/hatif03/storybound/trails), [runners](https://entire.io/gh/hatif03/storybound/runners), [sessions](https://entire.io/gh/hatif03/storybound/sessions), [analytics](https://entire.io/gh/hatif03/storybound/analytics).
- **Checkpoints, progress and key decisions:** one commit per intent so each checkpoint maps to one change; every hardening record names its commit and checkpoint ([evidence/hardening](https://github.com/hatif03/storybound/blob/main/evidence/hardening/)); the submission checkpoint is [commit 1a96c19](https://entire.io/gh/hatif03/storybound/commit/1a96c19fd6f99c981f7e6b7cbbea715d25eb55d2) (checkpoint `01M4MJM5TRM7NE2F8FHFJ49NE6`). Decisions kept include the safety-word tiering ([HR-004](https://github.com/hatif03/storybound/blob/main/evidence/hardening/HR-004.md)), pipelined review with the honest result that time to first page did not improve ([HR-002](https://github.com/hatif03/storybound/blob/main/evidence/hardening/HR-002.md)), and the history rewrite after keys reached checkpoint refs ([note](https://github.com/hatif03/storybound/blob/main/evidence/history-rewrite/NOTE.md)).
- **entire-graph, finding code and assessing risky changes:** `graph impact` before touching the safety words ([story_safe_text](https://github.com/hatif03/storybound/blob/main/evidence/entire/20261010-1421-IST-graph-impact-story_safe_text.txt), [verify_scene_async](https://github.com/hatif03/storybound/blob/main/evidence/entire/20261010-1421-IST-graph-impact-verify_scene_async.txt)), seven `graph diff` runs after changes ([HR-001](https://github.com/hatif03/storybound/blob/main/evidence/entire/20261010-1716-IST-graph-diff-HR-001-04ffebb.json), [HR-004](https://github.com/hatif03/storybound/blob/main/evidence/entire/20261010-1953-IST-graph-diff-HR-004-748ce42.json), [the picture agent](https://github.com/hatif03/storybound/blob/main/evidence/entire/20261011-1300-IST-graph-diff-auto-pictures-touch-early-painting.json)), and `entire why` on the oath catalog and prompts ([catalog](https://github.com/hatif03/storybound/blob/main/evidence/entire/20261010-1953-IST-why-catalog.txt)).
- **Reviews and trails that improved the project:** `entire review general` found 5 issues on PR 1 (one a real evidence-builder bug), 8 on PR 2 (a missing fallback that would have turned a gateway outage into failed stories) and 7 real defects in our own failure fixes on PR 4 ([PR 1](https://github.com/hatif03/storybound/blob/main/evidence/entire/20261011-1010-IST-review-general-pr1.txt), [PR 2](https://github.com/hatif03/storybound/blob/main/evidence/entire/20261011-1415-IST-review-general-pr2.txt), [PR 4](https://github.com/hatif03/storybound/blob/main/evidence/entire/20261012-IST-review-general-pr4.txt)). The trail runners flagged a chaos-injection setting that could reach production (fixed in [commit 5f9253b](https://entire.io/gh/hatif03/storybound/commit/5f9253b5de587701524983d4d91776a2d1798b05)) and an autoplay rule conflict (resolved by writing the rule precisely, [WEB.md](https://github.com/hatif03/storybound/blob/main/docs/WEB.md)). Trails on Entire: [2](https://entire.io/gh/hatif03/storybound/trails/2), [3](https://entire.io/gh/hatif03/storybound/trails/3), [4](https://entire.io/gh/hatif03/storybound/trails/4), [5](https://entire.io/gh/hatif03/storybound/trails/5).
- **Open-source builds on Entire's CLI, Graph or External Agents:** we did not contribute code to Entire's own repositories. We built on top of them: six Trail runners tailored to this project's hard rules in [.entire/runners](https://github.com/hatif03/storybound/tree/main/.entire/runners), custom key redactions after a key reached a checkpoint, Claude Code with commit linking `always`, and evidence scripts ([build_evidence.py](https://github.com/hatif03/storybound/blob/main/scripts/build_evidence.py), [lint_evidence.py](https://github.com/hatif03/storybound/blob/main/scripts/lint_evidence.py)) that read checkpoints and traces. Gaps we hit are documented in [TOOLS.md](https://github.com/hatif03/storybound/blob/main/docs/TOOLS.md).

### cfo.ai: how did it shape your business plan?
cfo.ai turned "what does a story cost?" into product decisions ([public model](https://app.cfo.ai/s/vGE_ZEwfQtpoxPrg), [BUSINESS.md](https://github.com/hatif03/storybound/blob/main/docs/BUSINESS.md)):
- **Pictures:** painting every page leaves a 43.4% month-6 margin against our 60% bar; half the pages clears it at 67.8%. So the agent now spends a fixed picture budget on the pages that matter most ([HR-010](https://github.com/hatif03/storybound/blob/main/evidence/hardening/HR-010.md)).
- **Measured cost:** the cost input is the number neatlogs measured, not a guess; Version history shows the edit ([screenshot](https://github.com/hatif03/storybound/blob/main/evidence/cfo/20261012-1332-IST-cfo-version-history-unit-economics.png)).
- **Video AI:** four scenarios showed three of the cheapest clips taking the margin from 67% to minus 70%, so video is left out and motion stays deterministic and checked.
- **A real launch:** a launch plan with operating and one-time costs (labelled as assumptions): about 2,490 paying households at $6.99 to break even. Workbooks: [evidence/cfo](https://github.com/hatif03/storybound/blob/main/evidence/cfo/), [screenshots](https://github.com/hatif03/storybound/blob/main/evidence/dashboards/cfo.ai/).

## Before you submit (in this order)
1. Merge PR 4 into `main` (it carries the experiments, drills, fixes, docs and the recording tools). Ask Claude to do it if you want.
2. Run `python scripts/build_evidence.py` and `python scripts/lint_evidence.py` (0 FAIL expected; the demo video check passes once the final video is in `evidence/demo/` and is at most 3:00).
3. Rotate the neatlogs and hackathon gateway keys (STATUS item 1) after the last run that needs them.
4. Upload the video, open the link in a private window, copy it into the tweet and the form.
5. Post the quote-tweet (19:00 onward), then fill the form, then log both in `evidence/posts.md`.

## "Tell your unique story in your own words" (use as few words as you can)
Short (about 55 words):
> AI can write a child's story in seconds, and nobody checks it. In our test, 27 of 28 stories broke a promise. Storybound writes its promises first, checks every page before the child sees it, rewrites what breaks, and hands the parent a receipt: 0 of 28. Built solo in three days, traced with neatlogs, tracked with Entire, priced with cfo.ai.

Shorter (about 30 words):
> Storybound turns a child's drawing into a story and checks every page against promises it wrote first, so a parent doesn't have to. Without checks, 27 of 28 stories broke a promise; with them, none.

Add one personal sentence of your own if you like (why you wanted this); I have not invented one.
