"""API tests: the pipeline is stubbed so no network is touched."""

from __future__ import annotations

import io
import json

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from storybound import api, pipeline


@pytest.fixture
def client(monkeypatch):
    def fake_execute(run):
        run.emit("run.started", {"story_id": run.story_id})
        run.emit("character.ready", {"card": {"name": "Benny"}})
        run.emit("run.finished", {"outcome": "shipped", "story_id": run.story_id})
        run.bus.close()
        return run

    monkeypatch.setattr(api, "execute", fake_execute)
    api.RUNS.clear()
    return TestClient(api.app)


def png() -> bytes:
    b = io.BytesIO()
    Image.new("RGB", (200, 200), "white").save(b, "PNG")
    return b.getvalue()


def test_reference_endpoints(client):
    assert client.get("/api/health").json()["ok"] is True
    ls = client.get("/api/lessons").json()
    assert {x["id"] for x in ls} == {"sharing", "honesty", "kindness", "patience"}
    fx = client.get("/api/fixtures").json()
    assert any(f["id"] == "benign/bunny-bow-carrot" and f["kind"] == "benign" for f in fx)
    assert client.get("/api/fixtures/benign/bunny-bow-carrot/image").status_code == 200
    assert client.get("/api/fixtures/../../secrets/image").status_code == 404


def test_create_and_stream(client):
    r = client.post("/api/stories", data={"lesson_id": "sharing", "fixture_id": "benign/bunny-bow-carrot"})
    assert r.status_code == 202
    sid = r.json()["story_id"]
    with client.stream("GET", f"/api/stories/{sid}/events") as s:
        body = "".join(s.iter_text())
    assert "event: run.started" in body and "event: run.finished" in body
    state = client.get(f"/api/stories/{sid}").json()
    assert state["status"] == "finished" and state["card"]["name"] == "Benny"


def test_validation_errors_are_calm_json(client):
    r = client.post("/api/stories", data={"lesson_id": "nope", "fixture_id": "benign/bunny-bow-carrot"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "unknown_lesson"
    r = client.post("/api/stories", data={"lesson_id": "sharing", "age": 12, "fixture_id": "benign/bunny-bow-carrot"})
    assert r.status_code == 422
    r = client.post("/api/stories", data={"lesson_id": "sharing"})
    assert r.json()["error"]["code"] == "bad_input"
    r = client.post(
        "/api/stories", data={"lesson_id": "sharing"}, files={"drawing": ("x.png", b"not an image", "image/png")}
    )
    assert r.status_code == 422 and r.json()["error"]["code"] == "bad_input"
    assert client.get("/api/stories/missing").status_code == 404


def test_upload_accepted(client):
    r = client.post(
        "/api/stories",
        data={"lesson_id": "kindness", "hero_name": "Mia"},
        files={"drawing": ("d.png", png(), "image/png")},
    )
    assert r.status_code == 202


def test_busy_when_slots_full(client, monkeypatch):
    monkeypatch.setattr(
        api,
        "_slots",
        type("S", (), {"acquire": lambda self, blocking=False: False, "release": lambda self: None, "_value": 0})(),
    )
    r = client.post("/api/stories", data={"lesson_id": "sharing", "fixture_id": "benign/bunny-bow-carrot"})
    assert r.status_code == 429 and r.json()["error"]["code"] == "busy"


def test_pipeline_module_has_run_config():
    assert pipeline.RunConfig(lesson_id="sharing").arm == "B1"
    assert json.dumps({"ok": True})
