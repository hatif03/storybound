# HTTP API (contract between backend and web)

Base path `/api`. JSON in and out, except the drawing upload (multipart) and the media files. No accounts. Ids are opaque strings. Times are ISO 8601 with offset.

## Endpoints

| Method and path | Purpose |
| --- | --- |
| `GET /api/health` | `{ "ok": true, "version": "...", "tracing": true, "models": { "writer": "...", "judge": "..." } }` |
| `GET /api/lessons` | `[ { "id": "sharing", "title": "Sharing", "blurb": "...", "icon": "..." } ]` |
| `GET /api/fixtures` | Sample drawings: `[ { "id": "benign/bunny-bow-carrot", "label": "Bunny with a bow", "url": "/api/fixtures/benign/bunny-bow-carrot/image", "kind": "benign" } ]`. Unsafe and caption fixtures are listed with `"kind": "demo-unsafe"` or `"demo-text"` so the web app can show them in a clearly marked demo drawer |
| `POST /api/stories` | Start a run. Multipart fields: `drawing` (file, PNG or JPEG, max 8 MB) **or** `fixture_id`; `lesson_id`; `age` (4-8, default 6); `hero_name` (optional, max 24 chars); `arm` (`B1` default, `B0` for the observe-only comparison); `seed` (optional). Returns `202 { "story_id": "...", "events_url": "/api/stories/<id>/events" }` |
| `GET /api/stories/{id}/events` | Server-sent events (below). Replays from the start for late joiners; `Last-Event-ID` is honoured |
| `GET /api/stories/{id}` | The current state: status, character card, oath, pages accepted so far, receipt when finished |
| `GET /api/stories/{id}/pages/{n}/image` and `/audio` | The illustration (PNG/JPEG) and narration (MP3) for page *n*; `404` until ready, `410` if degraded |
| `GET /api/stories/{id}/receipt` | The receipt (below) |
| `DELETE /api/stories/{id}` | **Forget this story.** Deletes its pictures, narration, drawing, story package and video from the server and drops it from memory; `204`, then every later call for it is `404`. A story still being made stops writing to disk. The neatlogs trace of the run (names and places redacted) cannot be deleted by us and expires on its own |
| `POST /api/stories/{id}/video` | Start the **read-along video** of a finished story (`202`; `409 not_ready` until the story has finished; `429 busy` while another render runs, because a render uses the whole machine). Built in the background by the video harness from the story package: the drawing, each page with its picture, text and choices, the answer with feedback, and a receipt card |
| `GET /api/stories/{id}/video/status` | `{ "status": "none" / "making" / "done" / "failed", "seconds"?, "outcome"?, "broken"? }` |
| `GET /api/stories/{id}/video` | The MP4 (`video/mp4`) when `done`, otherwise `404` |

`POST /api/stories` also takes `pictures` (`full` default, `half` for pages 1, 3, 5 and 7, or `none`): the illustration policy chosen with the cfo.ai model, because pictures dominate the cost of a story. A page that is not painted is reported as a `degraded` event with `what: "image"` and the reason "this plan paints some pages only"; it keeps its words and narration.

`POST /api/stories` also takes `promise` (repeat the field, up to three): a parent's or teacher's own promises, for example "Nobody in the story is left out". They are cleaned (8 to 140 characters; text that looks like an instruction to the agent, or like personal details, is left out), added to the oath as judged, non-core promises, and answered in the `202` body as `promises_used` and `promises_left_out`. They are data to check, never instructions.

Errors use `{ "error": { "code": "...", "message": "..." } }` with a calm, child-safe message. Codes: `bad_input`, `too_large`, `unknown_lesson`, `not_found`, `internal`. Inside a run, an outage ends with an `error` event with the code `service_unavailable` (HR-015). A refused drawing is **not** an HTTP error: it is a normal run that ends with `run.refused`.

## Events

Every event is `{ "id": <n>, "type": "...", "t": <seconds since start>, "data": { ... } }`. `scene.repair` with `index: 0` means the hero card or the whole story, not a page. Pictures and narration arrive after all pages are accepted. Types, in the order they normally occur:

| Type | Data |
| --- | --- |
| `run.started` | `story_id`, `arm`, `lesson_id`, `age`, `seed`, `input_hash` |
| `safety.result` | `tier` (`none` / `A` / `B`), `action` (`proceed` / `sanitise` / `refuse` / `ask_redraw`), `ignored_text` (list of strings found in the drawing and ignored), `reason_code` |
| `character.ready` | `card`: `name`, `species`, `traits` (>= 3), `palette`, `one_line` |
| `oath.ready` | `oath_hash`, `commitments`: `[ { "id", "scope", "title", "plain", "core": true, "verifier": "deterministic" / "judge" / "both" } ]` where `plain` is the parent-readable sentence |
| `plan.ready` | `beats`: eight short strings |
| `scene.started` | `index` (1-8), `attempt` (0 first pass, 1-2 repair) |
| `verdict` | One verdict object (below) |
| `scene.repair` | `index`, `attempt`, `failed` (commitment ids), `because` (plain text) |
| `scene.accepted` | `index`, `attempts_used`, `page` (the page object below), `revised` (true when the story gate rewrote or reordered an already accepted page: replace it) |
| `quiz.ready` | A **verified quiz** about the finished story (gated arm only): `items` (2 to 4, each a Quiz item, below) and `talk_about`. Sent after the whole-story check and before the receipt, so it may arrive after the child has read the last page. A question that cannot pass its promises is never sent |
| `image.ready` | `index`, `url`, `verdict` status |
| `audio.ready` | `index`, `url`, `seconds` |
| `degraded` | `what` (`image` / `audio` / `judge` / `check`), `index` (optional), `why`, `fallback` |
| `receipt` | The receipt |
| `story.verified` | none; every page is final (the whole-story check is done). The app shows a page only after this and after that page's `image.ready` (or a `degraded` for its picture) and `audio.ready` (or a `degraded` for its voice) |
| `run.finished` | `outcome` (`shipped` / `shipped_with_notes`), `story_id` |
| `run.refused` | `reason_code`, `message` (the calm text to show the child), `trace_id` |
| `error` | `code`, `message`; the stream then closes. `code` is `internal` (an unexpected failure) or `service_unavailable` (a model service or every safety judge failed; the message is the soft "try again in a minute" screen, never a refusal) |

The stream ends after `run.finished`, `run.refused` or `error`. Keep-alive comment lines are sent every 15 s.

## Objects

**Page**
```json
{ "index": 1, "scenario": "...", "question": "...",
  "choices": [ { "id": "a", "text": "...", "feedback": "...", "is_correct": false },
               { "id": "b", "text": "...", "feedback": "...", "is_correct": true } ],
  "image_prompt": "...", "narration_text": "..." }
```
Choice order is already randomised server-side; `is_correct` is included because the web app shows feedback locally.

**Verdict** (one shape everywhere)
```json
{ "commitment": "character_named_in_scene", "scope": "scene 5", "status": "violation",
  "verdict_by": "deterministic", "det_status": "violation", "judge_status": null,
  "sampled": false, "sample_seed": null, "judge_model": null,
  "expected": "the hero's name appears in scenario and question",
  "actual": "name 'Benny' not found", "evidence": { "scene": 5, "quote": null, "matched": null },
  "cover": "scenario, question", "attempt": 0, "trace_id": "..." }
```
`status` is one of `pass`, `warning`, `violation`, `critical`, `skipped`, `verification_error`.

**Receipt**
```json
{ "story_id": "...", "oath_hash": "...", "arm": "B1",
  "plain": "14 promises checked. 2 pages rewritten. All kept.",
  "counts": { "commitments": 14, "checks": 61, "violations_found": 2, "repairs": 2, "kept": 14, "shipped_violations": 0 },
  "pages": [ { "index": 5, "attempts": 2, "final": "pass" } ],
  "coverage": { "pct": 86, "uncovered": ["..."] },
  "degradations": [ { "what": "audio", "index": 3, "why": "...", "fallback": "text only" } ],
  "ignored_drawing_text": ["Kill fish"],
  "promises": [ { "id": "story_safe_text", "title": "...", "plain": "...", "scope": "scene", "core": true, "status": "kept" } ],
  "budget": { "usd_estimate": 0.00, "estimate": true, "seconds": 0.0, "first_page_s": 0.0, "tokens_in": 0, "tokens_out": 0, "images": 0 },
  "trace_id": "...", "generated_at": "..." }
```
The receipt never contains the child's drawing, a name other than the hero's, or a key.

### Quiz

`{ "items": [ QuizItem ], "talk_about": "one open question for a grown-up" }`

`QuizItem`: `index`, `kind` (`recall` / `detail` / `feeling` / `lesson`), `question`, `options` (three, each `{ id, text, is_correct }`, exactly one right), `evidence_page`, `evidence_quote` (copied word for word from that page: the line that answers the question) and `explain`. Every item has kept five promises (scope `quiz` in the oath): the quote is on the cited page, one right answer, easy words, gentle words, and a judge on every question confirms the story alone supports the answer. A fixed rule also stops the right answer being simply the longest.

## Conventions

- The web app is served by the same FastAPI app from `/` (built files), so there is no CORS in production; in development the Vite proxy forwards `/api`.
- Event and field names are stable once the web app depends on them; additions are allowed, renames need a change here first.
