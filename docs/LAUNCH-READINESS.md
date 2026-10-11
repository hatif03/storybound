# If this were launched to real children: the situations we thought of, and what is done

Written Sun 11 Oct 2026. Ages 4 to 8, a tablet, a parent nearby and sometimes not. Each row says what can go wrong, what the product does, and how we know. **Status** is one of: **built and tested** (a test or a browser check exists), **built** (in the code, checked by hand or by a run), **policy** (a rule written down, no code), **open** (not done). Research behind the evaluation rows: [research/evals-and-observability.md](research/evals-and-observability.md).

## 1. Hands, screens and devices

| Situation | What the product does | Status | Check |
| --- | --- | --- | --- |
| A palm, elbow or sleeve lands on the screen | Touch contacts wider than 60 px are not taps; three or more fingers down at once means a resting hand, and clicks are dropped; on the drawing, a second finger never starts a second stroke | **built and tested** | `web/src/lib/touchGuard.test.ts` (7 tests), `web/scripts/e2e-touch.mjs` (palm draws nothing, two fingers make one stroke) |
| Safari on iPad does not report contact size | The size rule cannot work there, so the other rules carry it: hold to confirm, undo, saved drafts, pencil-first rejection | **built**; Safari itself **not tested** (no iPad in this build) | stated in `touchGuard.ts` |
| The Apple Pencil is in use and the hand rests on the glass | After the pencil was seen, touches on the drawing are ignored for 6 s (hovering counts) | **built** (pointer type `pen`); not tested with a real pencil | `DrawCanvas.tsx` |
| A tap meant for one screen lands on the next (the screen changed under the finger) | Clicks within 350 ms of a screen change are dropped | **built and tested** | `touchGuard.test.ts`; our own e2e scripts had to learn to wait |
| Accidentally leaving a story, stopping the making, making another story | The "yes" button must be **held** for 0.9 s (ring fills); "keep going" is a plain tap and has focus; keyboard and screen reader activate at once | **built and tested** | `e2e-touch.mjs`: a quick tap does not stop the story, a hold does |
| Accidentally clearing the drawing | "Start over" clears at once and **can be undone** ("Bring my drawing back"); unlimited undo | **built and tested** | `e2e-touch.mjs` |
| Reload, a tab the tablet threw away, pull-to-refresh | The drawing in progress is kept in this tab (sessionStorage, strokes only) and comes back; a story in progress is picked up again from the server by its id; both are deleted when the story starts / by Forget | **built and tested** (drawing); story resume **built**, tested at unit level only (needs a live server) | `e2e-touch.mjs` (reload keeps 3 strokes), `resume` tests |
| The browser's back swipe or button | Held in place: the same history entry is put back, the app's own arrows go back | **built and tested** | `e2e-touch.mjs` |
| Pinch-zoom, double-tap zoom, long-press menus, dragging a picture | Switched off outside text fields | **built** | `touchGuard.ts`, `screens.css` |
| The tab goes to the background (home button) | The voice stops | **built** | `touchGuard.ts` |
| Portrait and landscape, tablet and phone widths | Layouts exist for desktop, tablet landscape and portrait, phone | **built**; real devices **not tested** | `web/shots/` (gitignored), `docs/WEB.md` |
| Sound surprises (a loud sound in a quiet room) | Sound is **off** until a grown-up turns it on; nothing plays before a tap | **built** | `settings.ts` |
| Very small text, low vision, screen reader | Text size setting, focus moves to each screen's heading, labels on every control | **built**; no screen-reader run | `docs/WEB.md` |

## 2. The story agent, with a child in the loop

| Situation | What the product does | Status | Check |
| --- | --- | --- | --- |
| Pictures cost the most; not every page needs one | The agent paints the pages the planner scores as important within a picture budget (default four pictures); it stops painting if the picture service fails twice in a row or the story's budget is gone; the other pages keep words and voice, and Pip says so on the page; the receipt lists the plan | **built and tested** | `tests/test_pipeline.py` (3 tests), receipt field `picture_plan`, a live run (see TOOLS.md) |
| A page the agent chose not to paint looks broken | It says "Pip saved the paint for the big moments. Listen to this page!" | **built** | `Reader.tsx` |
| The picture or voice service fails or hits its quota | Retry, longer wait on a quota error, then text for that page, said on the receipt | **built and tested** | HR-007, trace `94db23729dac…` |
| An unsafe or frightening drawing | Refused with a kind message; only "tier A" is refused; text in the drawing is never obeyed | **built and tested** on 26 fixtures; one unsafe fixture only | `evidence/runs/*safety-eval*` |
| A grown-up types a promise that is really an instruction | Treated as data: cleaned, capped at three, judged like any other promise | **built and tested** | `tests/test_oath.py` |
| Same drawing twice | Different seed, different story; nothing is shared between stories | **built** | state is per story |
| Ages 4 and 8 | The reading-level limits exist per age; every real run was age 6 | **partly**; one run per age is on the list below | `regress.py` can take `--age` cases |
| A language other than English | Not tested; the word-count reading check is English | **open** | |
| A drawing that expresses sadness or fear (a hurt relative) | Not handled specially: a cheerful lesson story may be the wrong answer; needs a policy and a golden case | **policy needed** | research note, item 13 |
| A grown-up asks to delete everything | "Forget" deletes pictures, voice, drawing, movie on the server and the saved draft in the tab | **built and tested** | `tests/test_api.py` |
| A story that is half delivered and the connection drops | Pages already shown stay; the stream reconnects from the start and the reducer ignores what it has seen | **built**, unit-tested | `storyReducer.test.ts` |

## 3. Watching it, and proving it (neatlogs, Entire, cfo.ai)

| Situation | What we do | Status | Check |
| --- | --- | --- | --- |
| A change to a prompt makes things worse | A frozen set of 16 past failures re-run on current code, with **resolved / unresolved / error** kept apart (the SWE-bench idea); an Entire runner demands a before/after record and a regression table when prompts or promises change | **built**, first run in HR-008 | `scripts/regress.py`, `evidence/regression/`, `.entire/runners/trail-drift.json` |
| Tuning on the same drawings we report on | Drawings are now declared **tuning** or **holdout**; every ledger row carries `split` | **built**; holdout sweep in HR-008 | `src/storybound/ledger.py` |
| The judge changes its mind for the wrong reasons | Order and length bias test on the judge (OpenAI's two named pitfalls) | **built**, results in HR-008 | `scripts/judge_bias.py` |
| Nobody is told when something breaks | Seven neatlogs alert rules (critical safety stop, expensive story run, oath violation seen, quiz promise broken, words painted into pictures, slow story, plus one disabled) with email delivery to each user's own account email (a test alert was queued); other channels need a webhook | **partly** | `evidence/neatlogs/20261011-more-alerts-results.json` |
| A human must agree with the judge | A draft human evaluation exists in neatlogs; 20 verdicts still to label | **open** (needs a person) | evaluation `aea3e3ce-…` |
| What does support, safety review and compliance cost at small scale? | cfo.ai table "Launch operating costs" (all labelled assumed): about $2.60 per household per month, **37% of the $6.99 Household price** | **built**; numbers are placeholders | `evidence/cfo/README.md`, change 279306 and 279307 |
| A model provider stalls or throttles one request | Gemini calls are hedged: a call with no answer after 45 s is sent a second time (the 87 s stall); quota errors back off longer; the planner, quiz maker and picture-text check run on the gateway, so one provider's quota does not stop a whole story | **built**; stall effect not yet measured in a real stall | HR-011, HR-012, `docs/CREDITS.md` |
| What if video AI were added? | cfo.ai scenarios: three of the cheapest clips take the margin from 67% to -70%; as an add-on it needs about $2.25 a story | **modelled**, not built | `docs/BUSINESS.md` |
| Generated video of a child's drawing | Access checked (Veo on Vertex), one clip made, and the **clip oath** caught the drift (hero redrawn, bars in the frame) | **built as a check**; not in the product | [research/video-generation.md](research/video-generation.md), `scripts/clip_check.py` |

## 4. Rules we keep for children (and where each one lives)
- No accounts, ads, tracking, purchases, timers, lives, streaks or scores for the child; every game is skippable.
- Sound off by default; nothing plays before a tap.
- Nothing the child made is kept after Forget; the only things kept in the tab are the in-progress strokes and the id of the story in progress.
- Real children's drawings never enter the repository, traces, ledger or a third-party vendor without a parent's consent (CLAUDE.md rule 3); generated video sends a drawing to a vendor, so it stays off for real children until the vendor's terms are read.
- A promise broken on a page means the page is fixed before the child sees it; if it cannot be fixed, it ships with the break on the grown-ups' receipt, except safety, which never ships broken.

## 5. What we would do next (in order)
1. Test on a real iPad with a real pencil and a child's hands (the biggest unknown here).
2. A human labels 20 judge verdicts; report the agreement.
3. Ages 4 and 8 and one non-English drawing through the gate.
4. A policy for sad or distressed drawings.
5. Email or webhook on the two alerts, once the owner says where they go.
6. Video: one optional "my drawing wakes up" clip on the cover page, behind the clip oath, with a parent's consent and the vendor's terms read first.
