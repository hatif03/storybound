# EVIDENCE

Generated 2026-10-10 13:42 IST by `scripts/build_evidence.py` from `evidence/ledger.jsonl` (15 rows, 12 story runs) and the folders under `evidence/`. Do not edit by hand.

Each result is a triple: the commit that produced it, the Entire checkpoint of the session (when the session was recorded), and the neatlogs trace.

## 1. The agent improved: before and after, with numbers

No hardening record yet.


## 2. neatlogs traces

12 ledger rows carry a neatlogs trace id. Exported readbacks are in `evidence/traces/` (read through the neatlogs MCP server).

| What | Trace id | File |
| --- | --- | --- |
| spike-gemini-text-trace | `e16a18b5dbcb9cbcac0bd5371a8230f4` | [20261010-1256-IST-spike-gemini-text-trace.json](evidence/traces/20261010-1256-IST-spike-gemini-text-trace.json) |
| spike-gemini-vision-trace | `4c7153ad26291eb9cd8cedbeaca40f78` | [20261010-1256-IST-spike-gemini-vision-trace.json](evidence/traces/20261010-1256-IST-spike-gemini-vision-trace.json) |
| spike-guardrail-trace | `cc85389a110d01e9407cab538a777ba4` | [20261010-1256-IST-spike-guardrail-trace.json](evidence/traces/20261010-1256-IST-spike-guardrail-trace.json) |
| spike-k2-judge-trace | `faea948bb4924a0b1ddbe7bd260967e7` | [20261010-1257-IST-spike-k2-judge-trace.json](evidence/traces/20261010-1257-IST-spike-k2-judge-trace.json) |
| first-full-run-trace | `301911c89d3eb42738c51022ab863a22` | [20261010-1318-IST-first-full-run-trace.json](evidence/traces/20261010-1318-IST-first-full-run-trace.json) |
| detections-created | `` | [20261010-1327-IST-detections-created.json](evidence/traces/20261010-1327-IST-detections-created.json) |
| media-run-429-trace | `94db23729dac6323368749acba4be1cb` | [20261010-1340-IST-media-run-429-trace.json](evidence/traces/20261010-1340-IST-media-run-429-trace.json) |

## 3. A recovery run: an action failed, what the agent did next

Gated arm, media on, kindness lesson, rabbit-tree-rainbow fixture. Image generation returned 429 RESOURCE_EXHAUSTED for 4 of 8 pages while a sweep was also running; the agent degraded those pages to text only, said so on the receipt, and finished. Recovery evidence.

- File: [20261010-1340-IST-kindness-rabbit-B1-media-image-429-recovery.json](evidence/runs/20261010-1340-IST-kindness-rabbit-B1-media-image-429-recovery.json); neatlogs trace `94db23729dac6323368749acba4be1cb`
- Degradations on the receipt: 4 (`image`: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': '...) -> `text only`
- Receipt line: "19 promises checked. 7 pages rewritten. 2 could not be fully kept: age_reading_level, illustration_present."

Repair recoveries inside the story loop: 3 gated runs repaired at least one page (see the sweep report).

## 4. Safety screen and judge checks

- Safety screen over the 26 fixture drawings, `20261010-1318-IST-safety-eval.json`: {"total": 26, "matched": 24, "unsafe_refused": "1/1", "benign_wrongly_refused": 0}
- Safety screen over the 26 fixture drawings, `20261010-1319-IST-safety-eval-2.json`: {"total": 26, "matched": 25, "unsafe_refused": "1/1", "benign_wrongly_refused": 0}
- Judge with injected faults, `20261010-1334-IST-judge-eval.json`: {"pages": 8, "lesson": "sharing", "false_alarms": "0/8", "swap caught by correct_choice_teaches_lesson": "8/8", "off-topic caught by lesson_concept_in_scene": "8/8", "scary caught by story_safe_text": "8/8", "judge_errors": "0/88"}

## 5. neatlogs detections

- **Critical safety stop** (regex): A safety promise failed: unsafe drawing refused, or an unsafe page was quarantined (Status: critical).
- **Oath violation** (regex): A promise in the story's oath was broken on a page or in the story (a GUARDRAIL verdict with Status: violation). Repair runs follow.
- **Expensive LLM Call** (conditional): Flags single LLM calls costing more than $1.00
- **Slow LLM Response** (conditional): Flags LLM calls taking longer than 30 seconds
- **Execution Failed** (conditional): Detects execution failures across any span (status = ERROR)

## 6. Entire

- Commits: 23; with an `Entire-Checkpoint` trailer: 0.
- Graph output: [20261010-1325-IST-graph-diff-283a4cf-2c65fd7.json](evidence/entire/20261010-1325-IST-graph-diff-283a4cf-2c65fd7.json)
- Graph output: [20261010-1325-IST-graph-search-verify-repair.txt](evidence/entire/20261010-1325-IST-graph-search-verify-repair.txt)

## 7. cfo.ai business plan

Not yet linked.

## 8. Public posts and repository

- Posts logged with #neatHack: 1 ([evidence/posts.md](evidence/posts.md)).
- First commit 2026-10-10T13:41:49+05:30; latest 2026-10-10T13:41:49+05:30. Window check: `python scripts/lint_evidence.py`.
