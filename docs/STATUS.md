# Status: what is done, what is left, who must act

Updated Sun 11 Oct 2026 (IST). Submission window: Mon 12 Oct 19:00 to 23:55 IST (confirmed by the builder). Evidence for every line is in `EVIDENCE.md`, `evidence/` and the documents linked.

## 1. Done

| Area | State | Evidence |
| --- | --- | --- |
| Story agent (oath, pipelined review, repair, receipt; arms B0, B1, B2) | Done, 80 tests | [DESIGN.md](DESIGN.md), `sweep-2-p2` |
| Safety screen over 26 fixture drawings | 25/26 matched, the unsafe one refused, no benign refused | `evidence/runs/*safety-eval*` |
| Judge on injected faults | 24/24 caught, 0/8 clean flagged, 0/88 unverifiable | `evidence/runs/20261010-1334-IST-judge-eval.json` |
| Experiments and hardening | Seven sweeps, a holdout sweep, a frozen regression set; HR-001 to HR-013 written (HR-008 to HR-012 on 11 Oct: evaluation gaps, the clip oath, early pictures, the neatlogs review fixes, spreading work across providers) | `evidence/hardening/`, `evidence/reports/`, `evidence/regression/` |
| Recovery run | Image quota errors, story shipped as text on those pages, receipt said so | trace `94db23729dac6323368749acba4be1cb` |
| Pictures, narration, receipt | Real runs, two illustrated stories | `evidence/stories/` |
| Illustration policy | `pictures: full / half / none` (from the cfo.ai model) | API doc, `tests/test_pipeline.py` |
| Agent chooses the pages to paint (policy `auto`, default) | The planner scores each beat's importance; the agent spends a $0.16 picture budget on the best pages, starts each picture when its page is accepted, and stops painting after two failures in a row. First picture at 70 s instead of 278 s in a same-drawing comparison | HR-010, `tests/test_pipeline.py`, `evidence/runs/20261011-1130-IST-auto-pictures-early-bunny-sharing.json` |
| Small hands (touch safety) | Hold-to-confirm, ghost-tap and palm guards, drawing kept through a reload, undoable start over, story resume, back swipe held; 7 unit tests and 11 browser checks (demo mode); no real iPad yet | `docs/WEB.md`, `web/scripts/e2e-touch.mjs` |
| Evaluation practice (SWE-bench, OpenAI guides) | Judge bias test, frozen 16-case regression set, tuning/holdout split, holdout sweep | HR-008, `docs/research/evals-and-observability.md` |
| Generated video (Veo) | Access checked, one clip made, clip oath rejected it | HR-009, `docs/research/video-generation.md` |
| Launch readiness | Situations, what is built and what is open | `docs/LAUNCH-READINESS.md` |
| Model routing (hackathon credits) | The planner on Nova 2 Lite, the quiz maker and the picture-text check on Claude Haiku via the gateway; writer, oath author, character card and safety screen stay on Gemini (measured, HR-012); gateway spend $1.79 of $20 | [CREDITS.md](CREDITS.md), HR-012 |
| neatlogs second pass | Incident review; hedged retry for the 87 s stall, tiered "ignore all", a corrected quiz detection | [research/neatlogs-incident-review.md](research/neatlogs-incident-review.md), HR-011 |
| Business model beyond the hackathon | Video AI scenarios (margin -70% with three cheapest clips), a real-launch plan (about 2,490 households to break even at $6.99) | [BUSINESS.md](BUSINESS.md), `evidence/cfo/` |
| Verified quiz | Four questions per story, six promises, judge on every question, dropped if unverified | `docs/WEB.md`, sweep 7 below |
| Picture-order game, healthy-play rules | Done; skippable, no timers, streaks, scores or autoplay | `docs/WEB.md`, `web/scripts/e2e-quiz-mock.mjs` |
| Grown-up promises | Done, end to end (appears on the receipt) | API doc, `tests/test_oath.py`, browser run |
| Forget a story (`DELETE /api/stories/{id}`) | Done; the story 404s afterwards | `tests/test_api.py`, browser run |
| Read-along video from a story | Done: 3:37 and 3:45 renders, all promises pass | `evidence/stories/bunny-sharing-2/video/receipt.json` |
| Web app through a real browser | Two live runs. Run 1: drawing, 8 pages, movie, Forget. Run 2 (`--pictures half`, 11 Oct): pictures painted on pages 1, 3, 5, 7 only and narration on all 8; the quiz was offered on the end screen and played (4 questions, a wrong answer showed the story line); the receipt read "28 promises checked, 0 pages rewritten, all kept", with the grown-up promise and all six quiz promises kept | `web/scripts/e2e-real.mjs`, `evidence/runs/20261011-0910-IST-live-ui-half-pictures-quiz.json`, `evidence/screens/` |
| neatlogs | Traces, 7 detections, triage review, measured cost; one alert rule and one evaluation draft created through the CLI (cost alert rejected, see item 4) | [TOOLS.md](TOOLS.md) |
| Entire | 37+ checkpoints, graph diffs, Brain, runners tailored | [TOOLS.md](TOOLS.md) |
| cfo.ai | Model built; measured cost in (change 275839); share link checked anonymously | [TOOLS.md](TOOLS.md), `evidence/cfo/` |
| Crustdata | Used once, derived counts only | `evidence/cfo/20261011-0850-IST-market-note-crustdata.md` |
| Documentation | PROCESS, TOOLS, STATUS, PLATFORMS, DESIGN addendum, API, WEB, README, HANDOFF | this folder |

### Quiz quality (sweep `sweep-7-quiz`, gated arm, 7 drawings x 2 lessons x 2 seeds)
Across 26 completed stories (2 further jobs errored on a Vertex quota error and were re-run, see HR-007):

| Measure | Result |
| --- | --- |
| Questions generated | 104 (4 per story) |
| Questions that passed every quiz promise and were shown | **98 (94%)**; 6 dropped after two repair attempts |
| Repair rounds | 6 across the sweep |
| Stories that got a quiz (2 or more verified questions) | 26 of 26; 21 had all four questions |
| What failed first, by promise | `quiz_reading_level` 4, `quiz_answerable` 1 (judge said not supported), `quiz_answerable` 1 (judge could not verify, so the question is not shown) |
| Cost | token estimate $0.0204 per gated story with a quiz against $0.0162 without (about +$0.004, +26% of the text cost); one story takes about 40 seconds longer; neatlogs-measured quiz cost is not yet available because the newest traces had no cost populated when read |

The quote promise and the one-right-answer promise never failed on the first pass in this sample; the weakest point is reading level (answers over the word limit). Sample: age 6, English, 7 drawings x 2 lessons x 2 seeds, one story per cell; the quiz was also reviewed by hand on one story (`evidence/stories/bunny-sharing-2/quiz.json`). Ledger rows carry a `quiz` field (`made`, `kept`, `repairs`, `shown`).

### HR-007: quota errors (found by sweep 7)
[HR-007](../evidence/hardening/HR-007.md): two of the 28 jobs ended on a Vertex 429 at the first call; the retry now waits four times longer on a quota error and tries once more. Re-run of those two jobs: both shipped. Tiny sample; the test pins the behaviour.

## 2. Left, and who must act

### Only the builder can do these
| # | Item | Why it is blocked | What to do |
| --- | --- | --- | --- |
| 1 | **Rotate the neatlogs key and the hackathon gateway key** | Both were pasted into the session. The key text has been scrubbed from every ref (history rewrite, 11 Oct, see `evidence/history-rewrite/NOTE.md`) but GitHub may retain unreachable objects, and the session transcript on this machine still has them | Rotate (the builder said they will); update `.env` |
| 2 | **Entire Trails: branch, PR, runners, review** | Done: trail 2 https://entire.io/gh/hatif03/storybound/trails/2, PR #1, `entire review general` ran (5 findings, fixed); see `TOOLS.md` (Trails). **Left: merge PR #1** (docs fixes are only on the branch until then); the approvals gate needs a second reviewer | Check the trail and PR on entire.io and read the runner results |
| 3 | **Entire checkpoint link: confirm from your own private window** | The repo is public now. A clean headless browser (no cookies) rendered the commit page: [screenshot](../evidence/screens/20261011-1015-IST-entire-commit-link-anonymous.png). A "Log in" button is shown but the page content is visible | Submission link: `https://entire.io/gh/hatif03/storybound/commit/1a96c19fd6f99c981f7e6b7cbbea715d25eb55d2`, checkpoint id `01M4MJM5TRM7NE2F8FHFJ49NE6` (the commit and its trailer are on `main`) |
| 4 | **neatlogs: guest link, human review, triage cards** (seven alert rules with email delivery now exist, thresholds retuned; the three triage cards are handled)  | (Update: the cost alert "Expensive story run", metric `cost`, max above 0.8, was created after the operator was sent as `>`; `evidence/neatlogs/20261011-cost-alert-results.json`.) Earlier state: | The write sign-in worked (11 Oct): a **critical safety stop** alert rule and a draft **human evaluation of judge verdicts** were created through the CLI (`evidence/neatlogs/20261011-write-config-results.json`). The **cost-per-story alert** was rejected (`INVALID_ARGUMENTS`) and the login has since expired (`OAUTH_LOGIN_EXPIRED`) | Sign in again (`neatlogs auth login`), then retry the cost alert; create a guest link for one trace; run the human review on 20 verdicts |
| 5 | **cfo.ai UI steps** | The workbooks are saved (`evidence/cfo/workbook/`, five files); the Version-history screenshot is not | Screenshot Version history (change 275839) into `evidence/cfo/` |
| 6 | **`#neatHack` posts and the submission post** | Posting is the builder's act | Log each in `evidence/posts.md` (URL, time, what it shows); content ideas in `docs/planning/content.md` |
| 7 | **Demo video (last)** | Requested last | `scripts/make_video.py` with `requires_coverage` (see HANDOFF.md); at most 3:00 |
| 8 | **Publish** | Repo visibility is the builder's call | After rotation: `build_evidence.py`, `lint_evidence.py`, quote-post Mon 12 Oct 19:00 to 23:55 IST |

### Work that can still be done (not blocking)
| Item | Note |
| --- | --- |
| Price the quiz and video add-ons in cfo.ai | The quiz estimate (+$0.004) is a note in the B1 cost basis (change 279068); a separate row and the video add-on are not modelled |
| Judge-reviewed quiz questions from more stories and ages | All runs were age 6; the quiz was reviewed by hand on one story and measured by the promises on 28 |
| Safari, touch devices, screen reader | Not verified (see `docs/WEB.md`); the browser checks use desktop Edge |
| Ages other than 6; languages other than English | Ages 4 and 8 and four Hindi and Spanish captions were run once each (HR-013); stories are English only |

## 3. Known limits (said plainly)
- Fit to the hackathon's problem statement (an agent that completes a substantial task start to finish, each result guiding the next action) is argued in [QUALIFICATION.md](QUALIFICATION.md), including the honest limit that the stage order is a fixed graph with open-ended repair inside it.
- Costs of pictures and narration are list-price assumptions; neatlogs prices text only. The true figure is on the Google Cloud bill, which we have not read.
- The evidence videos are made from fixture drawings only. The sister's drawings and cutouts used by the launch video were removed from git history (with the builder's consent for the drawings) and live only in the gitignored `video/launch/img/` and `_private/` on the builder's disk, so the launch video cannot be re-rendered from a fresh clone.
- Early work (before 15:08 on 10 Oct) has no Entire checkpoint; `entire why` shows older code as human-written.
- The quiz was played live through the browser UI (run 2). The picture-order game was checked in demo mode only; in the live half-pictures run the pictures were not ready when the script looked, so the game was not offered then, and the movie step of run 2 was not completed because the script's wait exceeded a browser timeout (fixed in the script; the movie was completed in run 1).
- neatlogs retention on the free plan is 14 days; traces are exported to the repo.
- The judge (K2) is a different model family from the writer, but not a human; human agreement was not measured (item 4).

## 4. Risks
| Risk | Mitigation |
| --- | --- |
| Pasted keys (scrubbed from refs; may be cached on GitHub) | Rotate both |
| A model quota error ending a run | HR-007 backoff; the receipt states degradations |
| Render time for the movie (about 7 minutes for 3:45) | The API runs it in the background with a status endpoint; one render at a time |
| Judges cannot open the Entire link | Item 3 |
