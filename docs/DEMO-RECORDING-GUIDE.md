# Recording guide: our app, neatlogs, Entire and cfo.ai

Written for: the builder, who records the one demo video (at most 3:00, script in [DEMO-SCRIPT.md](DEMO-SCRIPT.md)). Four captures, each short; the script says which seconds of each to use.

**Who records what.** The app capture is already made by a script (below, with sound and a voice-over), so you only need to record the three dashboards. The dashboards are behind your own logins (neatlogs, Entire, cfo.ai); a script should not sign in as you, so you record them with OBS (it is in your taskbar) or Windows Game Bar (`Win + Alt + R`).

**Before you press record (all captures)**
- 1920 x 1080, browser zoom 100%, dark or light but the same for all three dashboards; close the bookmarks bar and other tabs.
- Hide what must not show: your email address (neatlogs, cfo.ai, Entire account menus), API keys, the `.env` file, `_private/`, any child's name. Do not open settings pages with keys.
- Move the mouse slowly, and pause one second on each thing you want a viewer to read. Record each segment as its own clip; do not try to do it in one take.
- Rehearse the clicks once without recording.

---

## 1. Our app (made for you, with sound and a voice-over)
Files in `evidence/app-capture/` (large video files are not committed; they stay on your disk):
- `app-walkthrough.mp4`: the whole recording at normal speed (about 14 minutes, 1440 x 810), with every sound the app made (Pip's voice, the narration of each page, the chimes, the quiet music) and a voice-over that explains what is happening.
- `app-walkthrough-cut.mp4`: the same with the waiting stretches (while the agent writes and checks the story, and while a page waits for its picture and voice) sped up 12 times and silent; about 9 minutes. Use this as the starting point, then cut it to about 45 seconds for the 3:00 video.
- `app-walkthrough-cues.txt`: what happens when, in the full-length file, for cutting by hand. `voiceover/` holds each voice-over line as its own mp3 and the text of each line (`manifest.json`), so you can re-record any line in your own voice and drop it in.

It is a real story, made while the recording runs (real models, about $0.45), not a mock. Every screen is shown only when everything for it exists (words, picture, voice), so the recording holds on Pip's making screen while pages are made; the cut speeds those holds up.

What the recording shows, in order:
| Moment | What is on screen | What the voice-over says |
| --- | --- | --- |
| Welcome | The home screen | What Storybound is, and that an agent checks every page against promises it wrote first |
| Drawing | A bunny drawn with the mouse | The child draws on the screen |
| Name, lesson | Pip picks a name; the lesson "Sharing"; a grown-up promise typed in | A grown-up chooses the lesson and can add a promise |
| Making your story | Pip, the hero, and the promises filling in | The oath, writing and checking each page, rewriting a page that breaks a promise, then the wait while pictures and voices are made |
| Reading | Page 1 with its picture and voice, a choice, a wrong answer or a right answer | A wrong answer is never a scolding |
| Pages 2 to 8 | Each page with its picture, narration, choices | Each page was checked; nothing is shown before it is complete |
| Quiz, order game, end | Four verified questions, the picture-order game, the talk-about card | Quiz questions that fail a check are dropped |
| Grown-ups, receipt | The sum gate and the receipt | How many promises were checked, pages rewritten, what could not be kept |
| Forget | The story deleted | The app forgets the story |

To make it again: start the server (`.venv\Scripts\python.exe -m uvicorn storybound.api:app --app-dir src --port 8000`), `.venv\Scripts\python.exe scripts\make_demo_voiceover.py` (only when the words in `web/scripts/demo-voiceover.json` change), `cd web; node scriptsecord-demo.mjs`, then `.venv\Scripts\python.exe scripts\compose_demo.py` (options: `--speed 12` for the cut). The browser that records has no sound card, so the script logs every sound the app plays with its exact time and the screen as timestamped frames; `compose_demo.py` puts each sound back at its time and turns the app's sounds down while the voice-over speaks. To use the app by hand: open http://127.0.0.1:8000, press "Let's go", draw with the mouse or a finger (a simple shape is fine), "Done!", pick a name, pick "Sharing", press "Yes!", wait for "Read page 1!", then read and answer; the grown-ups area is the small button in the corner (answer the multiplication to open it).

---

## 2. neatlogs dashboard (about 60 seconds in the video, the longest block)
Open https://app.neatlogs.com, project "Mohammad's project". Record these in order:
1. **Traces** list, filter workflow `create-storybook`. Open `640b8a6d6ed6cce8941ddab55139ffba` (a story after the tracing fix). Expand the tree: the `node.*` steps, then a `verify:...` GUARDRAIL span; click it and show the quoted text, the verdict, the judge model. Say: "every promise is one span with the words it relied on."
2. **Before and after the tracing fix.** Show the trace `f238415f0de63afe58fcbf9a32ff4f2a` (208 spans, two pictures) then `640b8a6d...` (225 spans, four pictures and eight picture checks). Use the span counts shown at the top of each trace. (If the dashboard has dropped the old trace, use [the saved span lists](../evidence/traces/) on screen instead.)
3. **Incidents** page: the three cards that opened on 12 Oct, each resolved with a note: "Resolve Infinite Repair Loop..." (our tracing fault, not a loop), "Investigate Latency and Quota Exhaustion in `illustrate`" (our own drill), "Enforce Structured JSON Outputs ... K2" (refuted by the span). Open the first one, scroll to its resolution note and its linked traces (the three-span fragments). Say what the incident feature did: it surfaced fragments that led to the tracing fix.
4. **A failure we caused and fixed:** search traces by tag `chaos`; show a stopped story from drill C4 (judge down, `1efb456ec688b4562947eb2f47cafaff`) next to the same drawing shipped after the failover (drill C4b, `6dea25bda8b4755209dd793c67a296ed`). Say: "zero of five before the failover, five of five after."
5. **Detections** page: "Picture has words painted in" with its hits (after the picture-words drill, trace `c2a67d3482bbdff5beb6df58a4daf92b`), "Oath violation", "Critical Violation Monitor".
6. **Alerts** (email delivery on) and **Evals**: the evaluation "Do you agree with this verdict?" with your answers, if you have given them. Say the agreement number only if the dashboard shows one.
7. **Analytics**: cost per story and latency, one screen.

## 3. Entire dashboard (about 25 seconds)
Open https://entire.io/gh/hatif03/storybound.
1. The **commits / checkpoints** list: each commit with its checkpoint. Click the checkpoint of a fix, for example the commit "Start judge calls and pictures from the workflow's context ...", and show the session transcript summary. Say: "one fix, one commit, one checkpoint."
2. **Trails**: the open trail for this branch (PR 4), its **runner results** (review and gates), and the PR's **review findings** (the ten points from `entire review general`; seven were real defects in our own fixes). Show one finding next to the commit that fixed it.
3. A terminal clip (15 seconds): `entire why src/storybound/oath/judge.py` and `entire brain recall "judge"` to show Brain facts. (Run them in the repo; they print file and checkpoint links.)

## 4. cfo.ai (about 25 seconds)
Open the shared model at https://app.cfo.ai (workspace "invisible-technologies").
1. **Unit economics** page, Main scenario: 77% gross margin for the Household plan at month 6.
2. **Verification and illustration policy**: "Verify all plus half the pictures: 67.8%; all eight pictures: 43.4%". Say: "this is the number that made the agent choose which pages to paint."
3. Open **Version history** (the clock icon) and point at "Edited cell `Cost input` = Text and verification B1 gated for Cost input basis": the cost estimate replaced by the neatlogs measurement. The two screenshots are saved: [Unit economics](../evidence/cfo/20261012-1332-IST-cfo-version-history-unit-economics.png) and [Verification policy](../evidence/cfo/20261012-1333-IST-cfo-version-history-verification-policy.png).
4. **Launch plan** and the **Video AI** scenario (margin to minus 70%). One second each.

---

## How the captures fit the three questions the video must answer
- **The problem the agent solves:** capture 1 (the receipt frame).
- **How cfo.ai and Entire were part of the project:** captures 4 and 3.
- **How neatlogs found and resolved the incidents:** capture 2, items 2, 3 and 4 (the three incidents, shown as before and after).

## Safety checks before you export
Play the final file once with the sound off and look for: an email address, a key, a repository secret, a surname, a child's face. The app capture uses a drawn bunny only.

When the final 3:00 video is made, put it in `evidence/demo/` (`scripts/lint_evidence.py` checks its length there); the app capture above lives in `evidence/app-capture/`.
