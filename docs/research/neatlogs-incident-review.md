# neatlogs incident review (window 10 Oct 06:00 UTC to 11 Oct 08:00 UTC)

Read on 11 Oct 2026 from the neatlogs MCP (project "Mohammad's project", free tier). Raw files are in `evidence/neatlogs/review-2/`. Trace ids are the first 12 characters. This review adds to `evidence/neatlogs/TRIAGE-REVIEW.md`; the three open triage cards are the same three and were not redone.

## What could and could not be read

- 79 of the 110 error traces were pulled (72%) and sorted by cause. 68 of them have full span detail. The rest are in the pool file only.
- `get_trace_context` does not return the error text of an errored span (status ERROR, empty output). The cause was read from `search_traces` snippets instead. For 15 error traces no error text exists in any indexed field, so their cause is a guess and is marked as one.
- The MCP rejects field projection and span filters ("not_enabled"), rejects broad queries ("Service Unavailable") and caps sessions (HTTP 429, wait about 80 s). Counts below come from narrower queries.
- The `waste` analytics view returns no rows. Nothing in it could be read.
- Sessions: `session_id` equals the trace id in every trace seen, so the sessions view has nothing to group.

## Fix now

1. **Two detections have never fired and are probably broken** ("Quiz question failed a promise", "Picture has words painted in"). Both ran a backfill over 1,299 traces with 0 flagged. After they were created at 03:12 UTC the ledger shows 24 quiz-question repairs in 20 runs (for example `5421ee090126`, `e3fc473c2ccd`, `b674a7508efd`). The saved patterns are `quiz_(...).{0,400}(violation|critical|verification_error)` and `image_no_text.{0,400}violation`. They run at "trace" level, while the verdict text sits in GUARDRAIL spans as `Commitment: quiz_x\nScope: ...\nStatus: violation` (several lines). Likely cause (a hypothesis): `.` does not cross line breaks, and the trace-level text is empty (the workflow output is always null, see HR-004). The working "Oath violation" rule uses `Status: violation` on `span_type GUARDRAIL`. Action: in the neatlogs dashboard set both to run on GUARDRAIL spans and use `Commitment: quiz_\w+[\s\S]{0,300}Status: (violation|critical|verification_error)` (and the same shape for `image_no_text`). Test by checking that the backfill flags the 20 quiz runs above. Two of the six alert rules depend on these two detections, so both are silent today.
2. **No alert can reach anyone.** Every rule read back has `channelMask` email false, slack false, webhookCount 0 (files `20261011-write-config-results.json`, `...-more-alerts-results.json`). They show in the dashboard only. Action: add one email or webhook channel to at least "Critical safety stop".
3. **Most traces are one-span orphans, which makes the headline numbers misleading.** In two 10-minute samples (10 Oct 12:30 and 11 Oct 07:10) the traces that mention the K2 judge were 36 orphans to 6 story traces, and 82 orphans to 13 story traces (about 86% orphans both times). An orphan has an empty workflow name, the model name as its root span and 1 span lasting 2 to 11 s. 1,832 of the 2,095 traces mention K2, so orphans are most of the project (exact share not counted). That is why p50 is 5.3 s while a story takes about 160 s, and why the 5.25% error rate and the 2,095 count do not describe stories. Cause not found: `src/storybound/oath/engine.py:189` and `pipeline.py:236,505,611` already copy `contextvars`, so the neatlogs span parent is probably not carried by that copy (hypothesis). Action: run one story and count root traces; fix the judge call so it joins the story trace; until then filter dashboards and alerts to workflow `create-storybook` with more than 10 spans. Smaller version of the same problem: standalone probe and eval calls are also traced alone (`84672c2c44e2` smoke test, `d705e66e2d99` K2 call, `1d57b0016612` judge-bias run); set `environment` (it is null on every trace) to `eval` or `test` for them in `src/storybound/tracing.py` or the app entry point.
4. **The 87 s Gemini stall (HR-005) is back and is the main latency cause.** HR-005 reverted to a 90 s timeout because the 42 later jobs showed no stall. On 11 Oct between 06:55 and 07:16 UTC 13 error traces had one `gemini-3.7-flash` call that ended at about 87 s with 504 "Deadline expired" (for example `6c8c28dda3c9`, `1092b1bbc158`, `d0bb16b76ed0`, `55bb3418fe6f`, `8e2a6a444965`). All shipped (retry worked). Stalls come in bursts: 9 traces on 10 Oct 07:58 to 09:47 (87 s), 8 at 37 s during the 40 s experiment (12:22 to 12:28), 1 at 14:20, then the 13 above on 11 Oct. That pattern fits the provider being slow for some minutes, not our timeout. Action: reopen HR-005 and run the hedged retry its own text proposes (start a second call after about 15 s and take the first answer), measured on the 11 Oct burst.
5. **429 on text is fixed; 429 on pictures is not.** Since HR-007 (commit `3a89004`, 03:13 UTC on 11 Oct) 8 traces had a text 429 and all 8 shipped; before it 2 sweep-7 jobs ended in `error`. Pictures are different: 8 traces had image 429s with 6 to 48 failed spans each (`c9a78b746d47` 48 failed spans, 402 s; `aeea65c6b2cd` 31; `bcbaab155d9b` 32; `0fd459e70b51` 27), and `illustrate` failed 17 of 66 calls. The app falls back to text-only pages, so no child sees an error, but a story spends 3 to 5 minutes retrying (`node.media` 172 to 307 s). Action: after two image 429s in one story, stop painting for that story (the `auto` policy already stops after two failures; check it applies to the `full` and `half` policies too).
6. **Error spans without any error text (15 traces).** Gemini failures of 0.6 to 1.1 s (for example `182e4ea264be`, `9ac60464c282`, `33a9c06a4b76`, `57233238e74c`, `a32498d66523` all at 10 Oct 07:58 to 08:48 when three arms ran at once, and `21f5547097cb`, `2776b05792e0`, `83ec4cf94685` at 12:16 to 12:49) show ERROR but no message. Probably quota bursts, but unproven. Action: record exception type and message on every ERROR span in the model client wrapper.
7. **Three triage cards are still open** (`bdd1f6f1`, `ebcff17a`, `67e5d3bd`). Mark them resolved or archived in the dashboard with a link to `TRIAGE-REVIEW.md` (the CLI cannot write them). Evidence: `triage_open.json`.

## Watch

- **Parse errors persist.** 7 sampled traces mention a parse error, 3 of them on 11 Oct (`148a4920b0e0` 06:58, `e8a7ceeb2621` 07:01, `3d9e833be22b` 07:03). On 10 Oct two ended `error` (`e46e796a4a9e`, `06dac7f3455f`, "no JSON found in model output", the page JSON visibly unfinished); the 11 Oct ones shipped after a retry. A child sees nothing, but each costs a retry. Check whether the writer output is cut (limit 900 tokens in `agents/writer.py:97,145`) before changing anything.
- **Image cost is invisible in neatlogs.** For text-only stories neatlogs measures 28% more than the ledger estimate (133 matched traces: estimate 2.03 USD, measured 2.61 USD, median ratio 0.79). For stories with pictures it sees 11 to 18% of the cost: `0fd459e70b51` $0.0411 measured against $0.358 estimated; `a7dd9ae1b832` $0.0382 against $0.356; `94db23729dac` $0.0344 against $0.191. The cfo.ai change (275839) is labelled text and verification, which is correct; do not quote a neatlogs figure as the cost of an illustrated story. Window total 4.59 USD is text only.
- **The `make-video` traces** (10 traces, 4 to 8 minutes, 3 of the 4 slowest). In `1cf9255c913b` (532 s) the child spans add up to about 170 s (`narrate_scenes` 169 s); the other 360 s sit in no child span (probably rendering; not verified). One failed: `49953358144a` (10 Oct 11:56 UTC, the first preview, "five" not a number in the scene spec, 12 s; fixed since, later previews have no error).
- **Detections by day** (UTC; hourly files in `detection_trends.json`):

  | Detection | 10 Oct | 11 Oct (to 07:22) | Note |
  | --- | --- | --- | --- |
  | Oath violation | 585 | 24 | busiest hour 08:00 with 378 (three arms in parallel) |
  | Execution Failed | 298 | 14 | 111 in the 14:00 hour (image 429 runs) |
  | Slow LLM Response (over 30 s) | 171 | 14 | mostly the 87 s stalls and image calls |
  | Critical safety stop | 13 | 0 (3 more at 07:07 to 07:13 found by search, not yet in the trend) | see below |
  | Expensive LLM Call (over $1) | 0 | 0 | cannot fire at these prices |

  Counts follow the number of runs per hour, so they do not show effect by themselves. Per story, from the ledger (B1 violations found per run): p1 8.5, then p2 (HR-001, commit 13:40 IST) 1.8, p3 (HR-003, 17:46 IST) 0.8, then rising to 1.6 to 3.1 as new promises and harder holdout drawings were added. Ungated B0: 7.3 then 3.5. HR-001 and HR-003 are visible in the per-story numbers; neatlogs hourly counts alone could not show them.
- **Oath hits per story are normally 1 to 3.** About 9.7% of B1 runs end `shipped_with_notes` (18 of 185). That share, not the first-pass hit count, is what to watch.
- **`Execution Failed` is not "the story failed".** 58 of the 62 error traces matched to the ledger shipped (45 shipped, 13 shipped with notes); 4 ended `error`. A trace is "error" when any span errored, even if the retry worked.
- **`ignore all` is still a critical term.** `06a2527e2d27` (benign christmas tree, 10 Oct 08:57) stopped on "ignore all" in a story. HR-004 kept steering phrases critical on purpose; check that a phrase like "ignore all the noise" is not flagged in a benign story.

## Ignore, expected

- **The 13 Critical safety stop traces** (window to 07:03 UTC on 11 Oct; the 3 later ones are the Haiku ablation below):

  | Trace | When (UTC) | What fired | Verdict |
  | --- | --- | --- | --- |
  | `b8839d3c5c23`, `9226e2a194ba` | 10 Oct 07:49 | `evil-cat-knife-blood.png` refused (blood, weapon) in safety-eval and eval-2 | intended |
  | `2f7c60378c19` | 07:34 | 2-span test of the word "kill" | deliberate test |
  | `391a1ea14192` | 12:28 | `no_drawing_text_obedience`: "ignore" from the injection fixture appeared in the story; 1 repair, shipped | intended catch |
  | `196d160d19dd` (no ledger row), `94db23729dac`, `f43aac0962c1`, `11a2900d813d`, `76c35d5c7534`, `257acf701def`, `26fbc879cddb`, `a534baeb9d47` | 07:40 to 09:29 | `story_safe_text` on "fighting", "hurt", "hurts" in benign stories (rhinoceros, bunny, rabbit, mickey, injection fixtures) | false positives, all before HR-004 (commit 17:51 IST = 12:21 UTC) |
  | `06a2527e2d27` | 08:57 | "ignore all" in a benign christmas-tree story | false positive (still possible) |

  So 9 of 13 were false positives on benign text and 4 were intended. None of the 9 stopped a story (the ledger has no `stopped` outcome; the page was rewritten). After HR-004 there is no benign "hurt" stop in the window. The late 3 (`9a5f898abbec` 07:07, `c10ef4def317` 07:08, `4d8aca06c1a5` 07:13 on 11 Oct) come from the Claude Haiku screening ablation (`evidence/runs/20261011-1237-IST-safety-eval-haiku.json`): 1 is the intended unsafe fixture, 2 are Haiku refusing the benign-text fixtures `mild-insults-text` (hate_symbol) and `fish-kill-fish-caption` (violence). Not the production path.
- **Gemini 504 and 429 recovered by retry** (see Fix now 4 and 5): 58 of 62 matched error traces shipped.
- **Probe traces**: 9 error traces of 1 to 2 spans under 1.5 s are tests and probes (`84672c2c44e2`, `d705e66e2d99`, `9377b4373cb2`, `722715f50e8a`, `a1dc773730c7`, `d4244a031bd9`, `a399ec1dbdd8`, `5ee359c6569e`, `2de7e25d8acd`).
- **Two `neatlogs.doctor.v2` traces** (4 ms, zero cost) are the CLI doctor checks.
- **Expensive LLM Call** never fires and that is right: the most expensive whole trace is `aeea65c6b2cd` at $0.0602.

## 1. Error traces by cause (79 sampled of 110)

| Cause | Traces | Examples | Outcome |
| --- | --- | --- | --- |
| 504 Deadline expired, one Gemini text call stalls (87 s, or 37 s during the 40 s trial) | 29 | `20b89ff4b7cc`, `7ae65ad1592c`, `6c8c28dda3c9` | retry worked, all shipped |
| Fast Gemini failure 0.6 to 1.1 s, no error text (probably 429) | 15 | `182e4ea264be`, `9ac60464c282` | shipped |
| Probe or test traces | 9 | `84672c2c44e2`, `d705e66e2d99` | not stories |
| 429 on the image model | 8 | `c9a78b746d47`, `aeea65c6b2cd` | text-only fallback, shipped |
| 429 on Gemini text | 8 | `8e8b988aaeb9`, `05cbd7082ddc` | shipped (since HR-007) |
| Parse error, model output not JSON | 4 | `e46e796a4a9e`, `06dac7f3455f` | 2 ended `error` (10 Oct 08:02, 08:34), later ones shipped |
| K2 judge call failed, text not read (81 to 356 ms) | 3 | `76c35d5c7534`, `065d9c6ddcf6` | shipped |
| Our bug: page JSON missing `image_prompt` | 1 | `ac528975dda1` (07:55) | ended `error` |
| make-video spec validation | 1 | `49953358144a` | fixed |
| Unclassified | 1 | `1d57b0016612` | judge-bias test |

By day (sample): 54 on 10 Oct, 25 on 11 Oct. By ledger outcome: 45 shipped, 13 shipped with notes, 4 error, 17 with no ledger row (probes, the image runs from the web app, and other non-sweep runs). Not found in the sample: any 499 CANCELLED (the ledger has one, `eeb273a48602` on 11 Oct 05:25, retried since commit `81cdf96`), and any "refusal of an unsafe fixture" as an error: refusals are not errors.

## 2. Slowest 10 traces (all from the pool of 166; a trace not in it could be missing)

| Trace | Seconds | What dominated |
| --- | --- | --- |
| `20b89ff4b7cc` | 541 | 9 repairs, three 87.5 s stalls, a 115 s page write |
| `1cf9255c913b` | 532 | make-video, `narrate_scenes` 169 s, rest untraced |
| `c1e644106cb3` | 483 | two 87.6 s stalls, 7 repairs |
| `3d9e833be22b` | 475 | `node.media` 226 s: image 429 retries (`illustrate` 181 s) |
| `7ae65ad1592c` | 427 | 87.6 s stall inside a 145 s repair, 6 repairs |
| `f21e0b420aa8` | 406 | make-video, narration 139 s |
| `c9a78b746d47` | 402 | `node.media` 307 s: 48 failed image spans |
| `27cf10c0fed8` | 397 | four 37 s stalls (40 s trial), 62 s oath step |
| `d0bb16b76ed0` | 395 | 14 repairs, 404 spans, 87.7 s stall |
| `eef22eafcc69` | 392 | one 37 s stall, 4 repairs |

Reading: a stall or image retry was the biggest single block in 8 of 10. Repairs add time but each repair call is normal speed. A repair loop never ran away: the most repairs in one trace was 14 (`d0bb16b76ed0`, copyrighted-character fixture, shipped with notes).

## 3. Most expensive 10 and span counts

Top by measured cost: `aeea65c6b2cd` $0.0602 (376 spans, 83 LLM calls, 31 failed image spans), `3d9e833be22b` $0.0469, `d0bb16b76ed0` $0.0452, `bcbaab155d9b` $0.0417, `5c93dce96f57` $0.0412 (352 spans, 8 repairs, success), `0fd459e70b51` $0.0411, `c9a78b746d47` $0.0396, `a7dd9ae1b832` $0.0382, `5421ee090126` $0.0356, `5c3485166903` $0.0349. The costliest cluster is image-retry stories and heavy-repair stories, all bounded. Most spans: `d0bb16b76ed0` 404, `aeea65c6b2cd` 376, `3d9e833be22b` 374. Nothing unbounded; none near the $0.80 alert.

## 4. Did counts fall after our changes?

| Change (commit time, IST) | What the data shows |
| --- | --- |
| HR-001 prompt p2 (13:40) | B1 violations per story 8.5 to 1.8 (sweep 1 to 2) |
| HR-002 pipelined review (13:40) | not visible in neatlogs counts; the ledger decides it |
| HR-003 target two words under (17:46) | 1.8 to 0.8 per story (sweep 4); later 1.6 to 3.1 with more promises |
| HR-004 mild terms rewrite (17:51) | benign critical stops: 9 before, 0 after |
| HR-005 40 s timeout, reverted 18:28 | stalls moved from 87 s to 37 s and came back at 87 s on 11 Oct; not a fix |
| HR-006 `image_no_text` promise (18:56) | detection never fired; see Fix now 1, so no data |
| HR-007 429 back-off (08:43 on 11 Oct) | text 429: 8 traces, 0 ended `error` (2 before) |
| HR-010 early painting (11:20 on 11 Oct) | outside the window |

HR-008 to HR-009 are evaluation and video work and have no neatlogs trend. The two newest detections have no readable trend (`get_detection_trend` says "no detection found" for them, and also for "Expensive LLM Call" on a daily view; the tool matches names unreliably).

## 5. The six alert rules against what happened

| Rule (setting) | Real data | Verdict | Proposed |
| --- | --- | --- | --- |
| Critical safety stop (1 in 60 min, critical) | 4 intended and 9 false in window; none benign since HR-004 | sensible, but fires on every safety eval and unsafe-fixture run | keep 1 in 60; give eval runs an `environment` tag and mute them; add an email channel |
| Oath violation seen (3 in 60 min) | busy hours 50 to 378, quiet hours 1 to 8; a normal story makes 1 to 3 | fires on almost every story and every sweep | change to 40 in 60 min as "something changed", or drop it and watch the `shipped_with_notes` share (alert if above 20% of a day's stories) |
| Quiz questions dropped (5 in 120) | detection never fires | silent | fix detection first (Fix now 1); then 5 in 120 is reasonable (24 repairs in 75 runs) |
| Words painted into a picture (2 in 120) | detection never fires; no repaint in the ledger | silent | fix detection first; keep 2 in 120 |
| Slow story (p95 latency above 300) | all-trace p95 167 s (orphans pull it down); stories only: B1 p95 381 s, p50 160 s; 5 of the 13 ledger run groups with 10 or more runs had a B1 p95 above 300 | would stay quiet on the all-trace figure and miss real slowness; unit of "300" not confirmed (assumed seconds) | scope it to workflow `create-storybook` with more than 10 spans, p95 above 450 s; confirm the unit in the dashboard |
| Expensive story run (max cost above 0.8) | highest trace $0.0602, 13 times below the limit | never fires | 0.10 on measured text cost; images are not in that figure (see Watch) |

## 6. Not looked at before

- **Model mix** (traces that mention the model): K2 1,832; gemini-3.7-flash 351; claude-haiku 90; nova-2-lite 30; gemini-3.1-flash-image 15; gemini-2.5-flash-image 6. The K2 figure is mostly orphan judge calls (Fix now 3). The 3.1 image model is tried first and 2.5 is the fallback on every image failure.
- **Tools view:** `illustrate` 17 errors in 66 calls (26%); `safety_screen` 281 calls, 0 errors; `narrate` 151 calls, 0 errors; `narrate_scenes` 13 calls, 0 errors, 64 s on average.
- **Window cost and time:** 4.59 USD (text only), 8.05 million tokens, 10 `make-video` traces cost 0.022 USD in total and averaged 242 s.
- **Detections never read before:** the two 11 Oct regexes (Fix now 1).
- **Window caveat:** the KPI baseline window (9 Oct) is empty, so no before and after exists from the KPI view.

## Files

Raw evidence: `evidence/neatlogs/review-2/` (`trace_pool.json`, `trace_detail*.json`, `error_causes.json`, `error_primary_cause.json`, `error_cause_search.json`, `critical_traces.json`, `critical_detail.json`, `detection_trends.json`, `hourly_counts.json`, `misc.json` with detection configs and model counts).
