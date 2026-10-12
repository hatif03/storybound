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
| Demo video (at most 3:00) | Script: [DEMO-SCRIPT.md](DEMO-SCRIPT.md); what to record: [DEMO-RECORDING-GUIDE.md](DEMO-RECORDING-GUIDE.md); the app capture is made. Upload as unlisted (YouTube or Drive set to "anyone with the link") and test the link in a private window | **open: you record the dashboards and cut it** |
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

## Before you submit (in this order)
1. Merge PR 4 into `main` (it carries the experiments, drills, fixes, docs and the recording tools). Ask Claude to do it if you want.
2. Run `python scripts/build_evidence.py` and `python scripts/lint_evidence.py` (0 FAIL expected; the demo video check passes once the final video is in `evidence/demo/` and is at most 3:00).
3. Rotate the neatlogs and hackathon gateway keys (STATUS item 1) after the last run that needs them.
4. Upload the video, open the link in a private window, copy it into the tweet and the form.
5. Post the quote-tweet (19:00 onward), then fill the form, then log both in `evidence/posts.md`.
