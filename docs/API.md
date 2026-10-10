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

Errors use `{ "error": { "code": "...", "message": "..." } }` with a calm, child-safe message. Codes: `bad_input`, `too_large`, `unknown_lesson`, `not_found`, `internal`. A refused drawing is **not** an HTTP error: it is a normal run that ends with `run.refused`.

## Events

Every event is `{ "type": "...", "t": <seconds since start>, "data": { ... } }`. Types, in the order they normally occur:

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
| `scene.accepted` | `index`, `attempts_used`, `page` (the page object below) |
| `image.ready` | `index`, `url`, `verdict` status |
| `audio.ready` | `index`, `url`, `seconds` |
| `degraded` | `what` (`image` / `audio` / `judge` / `check`), `index` (optional), `why`, `fallback` |
| `receipt` | The receipt |
| `run.finished` | `outcome` (`shipped` / `shipped_with_notes`), `story_id` |
| `run.refused` | `reason_code`, `message` (the calm text to show the child), `trace_id` |
| `error` | `code`, `message`; the stream then closes |

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
  "budget": { "usd": 0.00, "seconds": 0.0, "tokens_in": 0, "tokens_out": 0 },
  "trace_id": "...", "generated_at": "..." }
```
The receipt never contains the child's drawing, a name other than the hero's, or a key.

## Conventions

- The web app is served by the same FastAPI app from `/` (built files), so there is no CORS in production; in development the Vite proxy forwards `/api`.
- Event and field names are stable once the web app depends on them; additions are allowed, renames need a change here first.
