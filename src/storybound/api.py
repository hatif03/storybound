"""HTTP API (see docs/API.md). The web build, when present, is served from the same app."""

from __future__ import annotations

import json
import secrets
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from . import lessons, media, tracing
from .agents.character import clean_hero_name
from .config import ROOT, env, get_settings
from .events import EventLog
from .pipeline import Run, RunConfig, execute

FIXTURES = ROOT / "assets" / "test-drawings"
RUNS_DIR = ROOT / "runs"
WEB_DIST = ROOT / "web" / "dist"
MAX_CONCURRENT = int(env("STORYBOUND_MAX_RUNS", "3"))

RUNS: dict[str, Run] = {}
_slots = threading.BoundedSemaphore(MAX_CONCURRENT)


@asynccontextmanager
async def lifespan(_: FastAPI):
    tracing.init()
    yield
    tracing.flush()


app = FastAPI(title="Storybound", version="0.1.0", lifespan=lifespan)


def err(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


@app.exception_handler(HTTPException)
async def _http(_: Request, e: HTTPException):
    return err(e.status_code, "not_found" if e.status_code == 404 else "bad_input", str(e.detail))


@app.exception_handler(RequestValidationError)
async def _val(_: Request, e: RequestValidationError):
    return err(422, "bad_input", "Some of that information was not quite right.")


# ---- reference data --------------------------------------------------------------------------------------------------


def _fixture_index() -> list[dict]:
    expected = json.loads((FIXTURES / "expected.json").read_text(encoding="utf-8"))
    kinds = {
        "benign": "benign",
        "edge": "edge",
        "synthetic": "synthetic",
        "tier-a-unsafe": "demo-unsafe",
        "tier-b-text": "demo-text",
    }
    out = []
    for fid in expected:
        if fid.startswith("_"):
            continue
        folder, name = fid.split("/", 1)
        stem = Path(name).stem
        out.append(
            {
                "id": fid.rsplit(".", 1)[0],
                "label": stem.replace("-", " ").capitalize(),
                "url": f"/api/fixtures/{fid.rsplit('.', 1)[0]}/image",
                "kind": kinds.get(folder, folder),
                "file": fid,
            }
        )
    return out


def _fixture_path(fid: str) -> Path | None:
    for f in _fixture_index():
        if f["id"] == fid:
            p = (FIXTURES / f["file"]).resolve()
            return p if p.is_file() and FIXTURES.resolve() in p.parents else None
    return None


@app.get("/api/health")
def health():
    s = get_settings()
    return {
        "ok": True,
        "version": app.version,
        "tracing": bool(env("NEATLOGS_API_KEY")),
        "models": {"writer": s.models.writer, "judge": s.models.judge},
        "running": MAX_CONCURRENT - _slots._value,  # type: ignore[attr-defined]
    }


@app.get("/api/lessons")
def list_lessons():
    return [{"id": x.id, "title": x.title, "blurb": x.blurb, "icon": x.icon} for x in lessons.LESSONS.values()]


@app.get("/api/fixtures")
def list_fixtures():
    return [{k: v for k, v in f.items() if k != "file"} for f in _fixture_index()]


@app.get("/api/fixtures/{fid:path}/image")
def fixture_image(fid: str):
    p = _fixture_path(fid)
    if not p:
        raise HTTPException(404, "No such sample drawing.")
    return FileResponse(p)


# ---- stories ----------------------------------------------------------------------------------------------------------


@app.post("/api/stories", status_code=202)
async def create_story(
    lesson_id: str = Form(...),
    age: int = Form(6),
    hero_name: str | None = Form(None),
    arm: str = Form("B1"),
    seed: str | None = Form(None),
    fixture_id: str | None = Form(None),
    drawing: UploadFile | None = File(None),
):
    if lesson_id not in lessons.LESSONS:
        return err(422, "unknown_lesson", "That lesson is not one I know yet.")
    if not 4 <= age <= 8:
        return err(422, "bad_input", "Age should be between 4 and 8.")
    if arm not in ("B0", "B1"):
        return err(422, "bad_input", "Unknown arm.")
    if drawing is not None and drawing.filename:
        raw = await drawing.read(media.MAX_UPLOAD + 1)
    elif fixture_id:
        p = _fixture_path(fixture_id)
        if not p:
            return err(404, "not_found", "No such sample drawing.")
        raw = p.read_bytes()
    else:
        return err(422, "bad_input", "Please add a drawing.")
    try:
        d = media.prepare(raw)
    except media.BadDrawing as e:
        return err(413 if e.code == "too_large" else 422, e.code, str(e))
    if not _slots.acquire(blocking=False):
        return err(429, "busy", "I am busy making other stories. Please try again in a minute.")
    sid = secrets.token_hex(6)
    cfg = RunConfig(
        lesson_id=lesson_id, age=age, hero_name=clean_hero_name(hero_name), arm=arm,
        seed=seed or secrets.token_hex(3), media=env("STORYBOUND_MEDIA", "1") != "0",
        run_dir=RUNS_DIR / sid, fixture=fixture_id, ledger_name=None,
    )  # fmt: skip
    run = Run(cfg=cfg, drawing=d, bus=EventLog(), story_id=sid)
    RUNS[sid] = run

    def work():
        try:
            execute(run)
        finally:
            _slots.release()

    threading.Thread(target=work, daemon=True, name=f"story-{sid}").start()
    return {"story_id": sid, "events_url": f"/api/stories/{sid}/events"}


def _get(sid: str) -> Run:
    run = RUNS.get(sid)
    if not run:
        raise HTTPException(404, "I can't find that story.")
    return run


@app.get("/api/stories/{sid}/events")
def story_events(sid: str, request: Request):
    run = _get(sid)
    start = 0
    last = request.headers.get("last-event-id")
    if last and last.isdigit():
        start = int(last) + 1

    def gen():
        i = start
        while True:
            evs, done = run.bus.since(i, 15.0)
            if not evs and not done:
                yield ": keep-alive\n\n"
                continue
            for e in evs:
                i = e["id"] + 1
                yield f"id: {e['id']}\nevent: {e['type']}\ndata: {json.dumps(e, ensure_ascii=False)}\n\n"
            if done:
                return

    return StreamingResponse(
        gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@app.get("/api/stories/{sid}")
def story_state(sid: str):
    run = _get(sid)
    evs = run.bus.all()
    state: dict = {"story_id": sid, "status": "running", "arm": run.cfg.arm, "pages": [], "receipt": run.receipt}
    for e in evs:
        t, d = e["type"], e["data"]
        if t == "character.ready":
            state["card"] = d["card"]
        elif t == "oath.ready":
            state["oath"] = d
        elif t == "scene.accepted":
            state["pages"].append(d["page"])
        elif t == "safety.result":
            state["safety"] = d
        elif t in ("run.finished", "run.refused", "error"):
            state["status"] = {"run.finished": "finished", "run.refused": "refused", "error": "error"}[t]
            if t == "run.refused":
                state["refusal"] = d
    return state


@app.get("/api/stories/{sid}/receipt")
def story_receipt(sid: str):
    run = _get(sid)
    if not run.receipt:
        raise HTTPException(404, "The receipt is not ready yet.")
    return run.receipt


@app.get("/api/stories/{sid}/pages/{n}/{kind}")
def page_media(sid: str, n: int, kind: str):
    run = _get(sid)
    if kind not in ("image", "audio"):
        raise HTTPException(404, "No such file.")
    path = run.media_paths.get(f"{kind}:{n}")
    if path and Path(path).is_file():
        return FileResponse(path)
    if any(d.get("what") == kind and d.get("index") == n for d in run.degradations):
        return err(410, "degraded", "This page does not have a " + kind + ".")
    raise HTTPException(404, "Not ready yet.")


# ---- web build (optional) -----------------------------------------------------------------------------------------------

if WEB_DIST.is_dir():
    app.mount("/", StaticFiles(directory=WEB_DIST, html=True), name="web")
