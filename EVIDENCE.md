# EVIDENCE

Generated 2026-10-11 12:07 IST by `scripts/build_evidence.py` from `evidence/ledger.jsonl` (283 rows, 262 story runs) and the folders under `evidence/`. Do not edit by hand.

Each result is a triple: the commit that produced it, the Entire checkpoint of the session (when the session was recorded), and the neatlogs trace.

## 1. The agent improved: before and after, with numbers

- [HR-001: reading level broke on almost every page (prompt p1 to p2)](evidence/hardening/HR-001.md)
- [HR-002: gated stories took too long (pipelined review)](evidence/hardening/HR-002.md)
- [HR-003: the page writer kept overshooting the reading limit (prompt p2 to p3)](evidence/hardening/HR-003.md)
- [HR-004: a lesson saying "hurts trust" was a critical safety hit (neatlogs triage card)](evidence/hardening/HR-004.md)
- [HR-005: one Gemini call stalled for 87 s per trace (neatlogs triage card): tried a 40 s timeout, not kept](evidence/hardening/HR-005.md)
- [HR-006: the image model painted words into a child's picture](evidence/hardening/HR-006.md)
- [HR-007: a per-minute quota error ended a run (quota errors back off longer)](evidence/hardening/HR-007.md)
- [HR-008: we had never checked the judge for order and length bias, never frozen a past failure, and tuned and reported on the same drawings](evidence/hardening/HR-008.md)
- [HR-009: a generated video clip of a child's drawing needs its own oath (the first clip failed it)](evidence/hardening/HR-009.md)
- [HR-010: pictures arrived after the whole story, so a child read every page without them](evidence/hardening/HR-010.md)

- Sweep report: [20261010-1505-IST-sweep-2-p2](evidence/reports/20261010-1505-IST-sweep-2-p2.md)
- Sweep report: [20261010-1506-IST-sweep-1-p1](evidence/reports/20261010-1506-IST-sweep-1-p1.md)
- Sweep report: [20261010-1752-IST-sweep-4-p3](evidence/reports/20261010-1752-IST-sweep-4-p3.md)
- Sweep report: [20261010-1828-IST-sweep-5-hr45](evidence/reports/20261010-1828-IST-sweep-5-hr45.md)
- Sweep report: [20261010-1828-IST-sweep-6-t90](evidence/reports/20261010-1828-IST-sweep-6-t90.md)
- Sweep report: [20261011-0853-IST-sweep-7-quiz](evidence/reports/20261011-0853-IST-sweep-7-quiz.md)

### 20261010-1505-IST-sweep-2-p2

84 runs. Same drawings, lessons and seeds in both arms; pictures and narration off.

| Metric | B0 | B1 | B2 |
| --- | --- | --- | --- |
| Runs (errors) | 28 (0) | 28 (0) | 28 (0) |
| Refused or asked to redraw | 0 | 0 | 0 |
| Stories made | 28 | 28 | 28 |
| **Shipped with a broken promise** | **27/28 (96%)** | **0/28 (0%)** | **27/28 (96%)** |
| Broken promises shipped (total) | 97 | 0 | 110 |
| Stopped on a critical safety failure | 0 | 0 | 0 |
| A promise broken on the first pass | 27/28 (96%) | 19/28 (68%) | 27/28 (96%) |
| Drawing text reached the shipped story | 0/8 (0%) | 0/8 (0%) | 0/8 (0%) |
| Drawing text leaked on first pass | 0/8 (0%) | 0/8 (0%) | 0/8 (0%) |
| Repairs per story (mean) | 0 | 1.82 | 0.04 |
| Seconds per story (mean) | 150.3 | 142.7 | 170.5 |
| Seconds to first page (mean) | 57.2 | 51.1 | 63.9 |
| Estimated USD per story (mean) | 0.0083 | 0.0162 | 0.0198 |
| Tokens per story (mean) | 21,384 | 35,540 | 27,559 |
| Judge calls that could not verify | 3/500 (1%) | 7/601 (1%) | 1/490 (0%) |

## Broken on the first pass, by promise

| Promise | B0 | B1 | B2 |
| --- | --- | --- | --- |
| `age_reading_level` | 3 | 15 | 2 |
| `character_named_in_scene` | 1 | 0 | 0 |
| `correct_choice_position_balanced` | 22 | 0 | 24 |
| `correct_choice_teaches_lesson` | 4 | 1 | 3 |

### 20261010-1506-IST-sweep-1-p1

56 runs. Same drawings, lessons and seeds in both arms; pictures and narration off.

| Metric | B0 | B1 |
| --- | --- | --- |
| Runs (errors) | 28 (0) | 28 (3) |
| Refused or asked to redraw | 0 | 0 |
| Stories made | 28 | 25 |
| **Shipped with a broken promise** | **28/28 (100%)** | **8/25 (32%)** |
| Broken promises shipped (total) | 206 | 14 |
| Stopped on a critical safety failure | 0 | 0 |
| A promise broken on the first pass | 28/28 (100%) | 25/25 (100%) |
| Drawing text reached the shipped story | 0/8 (0%) | 0/8 (0%) |
| Drawing text leaked on first pass | 0/8 (0%) | 0/8 (0%) |
| Repairs per story (mean) | 0.11 | 8.8 |
| Seconds per story (mean) | 180.5 | 246.8 |
| Seconds to first page (mean) | n/a | n/a |
| Estimated USD per story (mean) | 0.0085 | 0.0150 |
| Tokens per story (mean) | 23,833 | 37,011 |
| Judge calls that could not verify | 4/553 (1%) | 4/620 (1%) |

## Broken on the first pass, by promise

| Promise | B0 | B1 |
| --- | --- | --- |
| `age_reading_level` | 26 | 25 |
| `correct_choice_position_balanced` | 21 | 0 |
| `correct_choice_teaches_lesson` | 1 | 0 |
| `lesson_concept_in_scene` | 20 | 1 |

### 20261010-1752-IST-sweep-4-p3

14 runs. Same drawings, lessons and seeds in both arms; pictures and narration off.

| Metric | B1 |
| --- | --- |
| Runs (errors) | 14 (0) |
| Refused or asked to redraw | 0 |
| Stories made | 14 |
| **Shipped with a broken promise** | **1/14 (7%)** |
| Broken promises shipped (total) | 1 |
| Stopped on a critical safety failure | 0 |
| A promise broken on the first pass | 8/14 (57%) |
| Drawing text reached the shipped story | 0/4 (0%) |
| Drawing text leaked on first pass | 0/4 (0%) |
| Repairs per story (mean) | 0.93 |
| Seconds per story (mean) | 76.7 |
| Seconds to first page (mean) | 35.6 |
| Estimated USD per story (mean) | 0.0144 |
| Tokens per story (mean) | 30,216 |
| Judge calls that could not verify | 3/288 (1%) |

## Broken on the first pass, by promise

| Promise | B1 |
| --- | --- |
| `age_reading_level` | 1 |
| `lesson_specific_carrot_prop_consistency` | 1 |
| `lesson_specific_joyful_exhaust_smoke` | 1 |
| `lesson_specific_mutual_happiness` | 1 |

### 20261010-1828-IST-sweep-5-hr45

14 runs. Same drawings, lessons and seeds in both arms; pictures and narration off.

| Metric | B1 |
| --- | --- |
| Runs (errors) | 14 (0) |
| Refused or asked to redraw | 0 |
| Stories made | 14 |
| **Shipped with a broken promise** | **1/14 (7%)** |
| Broken promises shipped (total) | 1 |
| Stopped on a critical safety failure | 0 |
| A promise broken on the first pass | 9/14 (64%) |
| Drawing text reached the shipped story | 0/4 (0%) |
| Drawing text leaked on first pass | 1/4 (25%) |
| Repairs per story (mean) | 1.57 |
| Seconds per story (mean) | 203.7 |
| Seconds to first page (mean) | 105.6 |
| Estimated USD per story (mean) | 0.0155 |
| Tokens per story (mean) | 37,008 |
| Judge calls that could not verify | 4/349 (1%) |

## Broken on the first pass, by promise

| Promise | B1 |
| --- | --- |
| `age_reading_level` | 1 |
| `lesson_specific_confession_relief` | 1 |
| `lesson_specific_hiding_visual_consequence` | 1 |
| `lesson_specific_honest_confession_dialogue` | 1 |

### 20261010-1828-IST-sweep-6-t90

14 runs. Same drawings, lessons and seeds in both arms; pictures and narration off.

| Metric | B1 |
| --- | --- |
| Runs (errors) | 14 (0) |
| Refused or asked to redraw | 0 |
| Stories made | 14 |
| **Shipped with a broken promise** | **1/14 (7%)** |
| Broken promises shipped (total) | 1 |
| Stopped on a critical safety failure | 0 |
| A promise broken on the first pass | 10/14 (71%) |
| Drawing text reached the shipped story | 0/4 (0%) |
| Drawing text leaked on first pass | 0/4 (0%) |
| Repairs per story (mean) | 1.93 |
| Seconds per story (mean) | 114.9 |
| Seconds to first page (mean) | 53.0 |
| Estimated USD per story (mean) | 0.0162 |
| Tokens per story (mean) | 39,177 |
| Judge calls that could not verify | 1/326 (0%) |

## Broken on the first pass, by promise

| Promise | B1 |
| --- | --- |
| `age_reading_level` | 1 |
| `lesson_concept_in_scene` | 1 |
| `lesson_specific_antenna_truth_signals` | 1 |
| `lesson_specific_cherished_carrot_truth` | 1 |

### 20261011-0853-IST-sweep-7-quiz

28 runs. Same drawings, lessons and seeds in both arms; pictures and narration off.

| Metric | B1 |
| --- | --- |
| Runs (errors) | 28 (0) |
| Refused or asked to redraw | 0 |
| Stories made | 28 |
| **Shipped with a broken promise** | **1/28 (4%)** |
| Broken promises shipped (total) | 1 |
| Stopped on a critical safety failure | 0 |
| A promise broken on the first pass | 20/28 (71%) |
| Drawing text reached the shipped story | 0/8 (0%) |
| Drawing text leaked on first pass | 0/8 (0%) |
| Repairs per story (mean) | 2.36 |
| Seconds per story (mean) | 153.7 |
| Seconds to first page (mean) | 46.7 |
| Estimated USD per story (mean) | 0.0201 |
| Tokens per story (mean) | 48,646 |
| Judge calls that could not verify | 2/799 (0%) |

## Broken on the first pass, by promise

| Promise | B1 |
| --- | --- |
| `age_reading_level` | 1 |
| `lesson_specific_antenna_joy_reaction` | 1 |
| `lesson_specific_antennae_waving_joy` | 1 |
| `lesson_specific_bubble_symbol_of_hiding` | 1 |

## 2. neatlogs traces

272 ledger rows carry a neatlogs trace id. Exported readbacks are in `evidence/traces/` (read through the neatlogs MCP server).

| What | Trace id | File |
| --- | --- | --- |
| spike-gemini-text-trace | `e16a18b5dbcb9cbcac0bd5371a8230f4` | [20261010-1256-IST-spike-gemini-text-trace.json](evidence/traces/20261010-1256-IST-spike-gemini-text-trace.json) |
| spike-gemini-vision-trace | `4c7153ad26291eb9cd8cedbeaca40f78` | [20261010-1256-IST-spike-gemini-vision-trace.json](evidence/traces/20261010-1256-IST-spike-gemini-vision-trace.json) |
| spike-guardrail-trace | `cc85389a110d01e9407cab538a777ba4` | [20261010-1256-IST-spike-guardrail-trace.json](evidence/traces/20261010-1256-IST-spike-guardrail-trace.json) |
| spike-k2-judge-trace | `faea948bb4924a0b1ddbe7bd260967e7` | [20261010-1257-IST-spike-k2-judge-trace.json](evidence/traces/20261010-1257-IST-spike-k2-judge-trace.json) |
| first-full-run-trace | `301911c89d3eb42738c51022ab863a22` | [20261010-1318-IST-first-full-run-trace.json](evidence/traces/20261010-1318-IST-first-full-run-trace.json) |
| detections-created | `` | [20261010-1327-IST-detections-created.json](evidence/traces/20261010-1327-IST-detections-created.json) |
| media-run-429-trace | `94db23729dac6323368749acba4be1cb` | [20261010-1340-IST-media-run-429-trace.json](evidence/traces/20261010-1340-IST-media-run-429-trace.json) |
| sweep2-b1-reading-level-scene7 | `a32498d665231ab02f7218b8b54e9a3f` | [20261010-1505-IST-sweep2-b1-reading-level-scene7.json](evidence/traces/20261010-1505-IST-sweep2-b1-reading-level-scene7.json) |
| sweep2-b1-reading-level-scene7-offset100 | `a32498d665231ab02f7218b8b54e9a3f` | [20261010-1506-IST-sweep2-b1-reading-level-scene7-offset100.json](evidence/traces/20261010-1506-IST-sweep2-b1-reading-level-scene7-offset100.json) |
| sweep2-b1-reading-level-scene7-offset50 | `a32498d665231ab02f7218b8b54e9a3f` | [20261010-1506-IST-sweep2-b1-reading-level-scene7-offset50.json](evidence/traces/20261010-1506-IST-sweep2-b1-reading-level-scene7-offset50.json) |
| sweep1-p1-bunny-sharing-B1-7-reading-level-repairs | `264208295ada9b28a96d2e29b32fb41c` | [20261010-1508-IST-sweep1-p1-bunny-sharing-B1-7-reading-level-repairs.json](evidence/traces/20261010-1508-IST-sweep1-p1-bunny-sharing-B1-7-reading-level-repairs.json) |
| sweep2-bunny-sharing-B1-pipelined | `a32498d665231ab02f7218b8b54e9a3f` | [20261010-1522-IST-sweep2-bunny-sharing-B1-pipelined.json](evidence/traces/20261010-1522-IST-sweep2-bunny-sharing-B1-pipelined.json) |
| sweep3-ahead1-bunny-sharing-B1-sequential | `e0d0e072d74ef1db7186b0cb445d744f` | [20261010-1522-IST-sweep3-ahead1-bunny-sharing-B1-sequential.json](evidence/traces/20261010-1522-IST-sweep3-ahead1-bunny-sharing-B1-sequential.json) |
| video-preview-4-make-video | `3ec11cfc58c141c00b7119c53a05b821` | [20261010-1741-IST-video-preview-4-make-video.json](evidence/traces/20261010-1741-IST-video-preview-4-make-video.json) |
| sweep4-p3-bunny-sharing-B1 | `2776b05792e0e7ef1bc47f12bc6df571` | [20261010-1752-IST-sweep4-p3-bunny-sharing-B1.json](evidence/traces/20261010-1752-IST-sweep4-p3-bunny-sharing-B1.json) |
| story-video-final-make-video | `5ebd6467432307ac1687fd7adb435fc2` | [20261010-1914-IST-story-video-final-make-video.json](evidence/traces/20261010-1914-IST-story-video-final-make-video.json) |

## 3. A recovery run: an action failed, what the agent did next

Gated arm, media on, kindness lesson, rabbit-tree-rainbow fixture. Image generation returned 429 RESOURCE_EXHAUSTED for 4 of 8 pages while a sweep was also running; the agent degraded those pages to text only, said so on the receipt, and finished. Recovery evidence.

- File: [20261010-1340-IST-kindness-rabbit-B1-media-image-429-recovery.json](evidence/runs/20261010-1340-IST-kindness-rabbit-B1-media-image-429-recovery.json); neatlogs trace `94db23729dac6323368749acba4be1cb`
- Degradations on the receipt: 4 (`image`: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': '...) -> `text only`
- Receipt line: "19 promises checked. 7 pages rewritten. 2 could not be fully kept: age_reading_level, illustration_present."

Repair recoveries inside the story loop: 128 gated runs repaired at least one page (see the sweep report).

## 4. Safety screen and judge checks

- Safety screen over the 26 fixture drawings, `20261010-1318-IST-safety-eval.json`: {"total": 26, "matched": 24, "unsafe_refused": "1/1", "benign_wrongly_refused": 0}
- Safety screen over the 26 fixture drawings, `20261010-1319-IST-safety-eval-2.json`: {"total": 26, "matched": 25, "unsafe_refused": "1/1", "benign_wrongly_refused": 0}
- Judge with injected faults, `20261010-1334-IST-judge-eval.json`: {"pages": 8, "lesson": "sharing", "false_alarms": "0/8", "swap caught by correct_choice_teaches_lesson": "8/8", "off-topic caught by lesson_concept_in_scene": "8/8", "scary caught by story_safe_text": "8/8", "judge_errors": "0/88"}
- Judge with injected faults, `20261010-1823-IST-judge-eval-claude-haiku.json`: {"pages": 8, "lesson": "sharing", "false_alarms": "0/8", "swap caught by correct_choice_teaches_lesson": "7/8", "off-topic caught by lesson_concept_in_scene": "8/8", "scary caught by story_safe_text": "8/8", "judge_errors": "3/88"}
- Judge with injected faults, `20261010-1823-IST-judge-eval-claude-sonnet.json`: {"pages": 8, "lesson": "sharing", "false_alarms": "0/8", "swap caught by correct_choice_teaches_lesson": "7/8", "off-topic caught by lesson_concept_in_scene": "8/8", "scary caught by story_safe_text": "8/8", "judge_errors": "1/88"}

## 5. neatlogs detections

- **Critical safety stop** (regex): A safety promise failed: unsafe drawing refused, or an unsafe page was quarantined (Status: critical).
- **Oath violation** (regex): A promise in the story's oath was broken on a page or in the story (a GUARDRAIL verdict with Status: violation). Repair runs follow.
- **Expensive LLM Call** (conditional): Flags single LLM calls costing more than $1.00
- **Slow LLM Response** (conditional): Flags LLM calls taking longer than 30 seconds
- **Execution Failed** (conditional): Detects execution failures across any span (status = ERROR)

## 6. Entire

- Commits: 31; with an `Entire-Checkpoint` trailer: 0.
- Graph output: [20261010-1325-IST-graph-diff-283a4cf-2c65fd7.json](evidence/entire/20261010-1325-IST-graph-diff-283a4cf-2c65fd7.json)
- Graph output: [20261010-1325-IST-graph-search-verify-repair.txt](evidence/entire/20261010-1325-IST-graph-search-verify-repair.txt)
- Graph output: [20261010-1421-IST-graph-impact-story_safe_text.txt](evidence/entire/20261010-1421-IST-graph-impact-story_safe_text.txt)
- Graph output: [20261010-1421-IST-graph-impact-verify_scene_async.txt](evidence/entire/20261010-1421-IST-graph-impact-verify_scene_async.txt)
- Graph output: [20261010-1421-IST-graph-verify-after.txt](evidence/entire/20261010-1421-IST-graph-verify-after.txt)
- Graph output: [20261010-1421-IST-graph-verify-baseline-v.txt](evidence/entire/20261010-1421-IST-graph-verify-baseline-v.txt)
- Graph output: [20261010-1421-IST-graph-verify-baseline.txt](evidence/entire/20261010-1421-IST-graph-verify-baseline.txt)
- Graph output: [20261010-1421-IST-graph-verify-pytest.txt](evidence/entire/20261010-1421-IST-graph-verify-pytest.txt)
- Graph output: [20261010-1716-IST-graph-diff-HR-001-04ffebb.json](evidence/entire/20261010-1716-IST-graph-diff-HR-001-04ffebb.json)
- Graph output: [20261010-1716-IST-graph-diff-HR-002-daec9ea.json](evidence/entire/20261010-1716-IST-graph-diff-HR-002-daec9ea.json)
- Graph output: [20261010-1745-IST-brain-brief-video-scene-type.json](evidence/entire/20261010-1745-IST-brain-brief-video-scene-type.json)
- Graph output: [20261010-1745-IST-brain-status.txt](evidence/entire/20261010-1745-IST-brain-status.txt)
- Graph output: [20261010-1953-IST-graph-diff-HR-003-31022e7.json](evidence/entire/20261010-1953-IST-graph-diff-HR-003-31022e7.json)
- Graph output: [20261010-1953-IST-graph-diff-HR-004-748ce42.json](evidence/entire/20261010-1953-IST-graph-diff-HR-004-748ce42.json)
- Graph output: [20261010-1953-IST-graph-diff-HR-006-7b2f310.json](evidence/entire/20261010-1953-IST-graph-diff-HR-006-7b2f310.json)
- Graph output: [20261010-1953-IST-why-catalog.txt](evidence/entire/20261010-1953-IST-why-catalog.txt)
- Graph output: [20261010-1953-IST-why-prompts.txt](evidence/entire/20261010-1953-IST-why-prompts.txt)
- Graph output: [20261010-1955-IST-checkpoint-tokens-HR-006-vs-HR-001-test.txt](evidence/entire/20261010-1955-IST-checkpoint-tokens-HR-006-vs-HR-001-test.txt)
- Graph output: [20261011-0925-IST-trail-1-created.txt](evidence/entire/20261011-0925-IST-trail-1-created.txt)
- Graph output: [20261011-1010-IST-review-general-pr1.txt](evidence/entire/20261011-1010-IST-review-general-pr1.txt)
- Graph output: [20261011-1010-IST-trail-2-show.json](evidence/entire/20261011-1010-IST-trail-2-show.json)
- Graph output: [20261011-1030-IST-trail-2-gates.json](evidence/entire/20261011-1030-IST-trail-2-gates.json)
- Graph output: [20261011-review-quiz-games.log](evidence/entire/20261011-review-quiz-games.log)
- Graph output: [baseline.json](evidence/entire/baseline.json)

## 7. cfo.ai business plan

- [20261010-1745-IST-cfo-inspect-history.json](evidence/cfo/20261010-1745-IST-cfo-inspect-history.json)
- [20261010-1745-IST-cfo-readback-main-growth-downside.json](evidence/cfo/20261010-1745-IST-cfo-readback-main-growth-downside.json)
- [20261011-0845-IST-share-link-anonymous-render.png](evidence/cfo/20261011-0845-IST-share-link-anonymous-render.png)
- [20261011-0850-IST-market-note-crustdata.md](evidence/cfo/20261011-0850-IST-market-note-crustdata.md)
- [20261011-1215-IST-launch-operating-costs-readback.json](evidence/cfo/20261011-1215-IST-launch-operating-costs-readback.json)
- [README.md](evidence/cfo/README.md)

## 8. Public posts and repository

- Posts logged with #neatHack: 1 ([evidence/posts.md](evidence/posts.md)).
- First commit 2026-10-10T12:30:17+05:30; latest 2026-10-11T12:01:15+05:30. Window check: `python scripts/lint_evidence.py`.
