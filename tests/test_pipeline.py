"""Offline end-to-end check of the graph wiring: fake agents, no network, judge off."""

from __future__ import annotations

import pytest

from storybound import media, pipeline
from storybound.agents import character, oath_author, planner, safety, writer
from storybound.events import EventLog
from storybound.models import CharacterCard, Choice, Page, Verdict
from storybound.oath import catalog

CARD = CharacterCard(name="Benny", species="rabbit", traits=["pink bow", "orange carrot", "round tail"])


THINGS = ["a berry", "a shell", "a kite", "a bell", "a marble", "a feather", "a cookie", "a ribbon"]
PLACES = ["pond", "hill", "barn", "river", "meadow", "cave", "bridge", "orchard"]


def good_page(i: int, slot: int, name: str = "Benny") -> Page:
    cs = [
        Choice(id="a", text="Keep it", feedback="Hmm.", is_correct=False),
        Choice(id="b", text="Share it", feedback="Yay.", is_correct=False),
    ]
    cs[slot].is_correct = True
    return Page(
        index=i,
        scenario=f"{name} has a pink bow and finds {THINGS[i - 1]} near the {PLACES[i - 1]}.",
        question=f"What will {name} do with it?",
        choices=cs,
        image_prompt=f"{name} the rabbit with a pink bow",
        narration_text="x",
    )


@pytest.fixture
def drawing():
    import io

    from PIL import Image

    im = Image.new("RGB", (300, 300), "white")
    for x in range(100, 200):
        for y in range(100, 200):
            im.putpixel((x, y), (200, 30, 30))
    b = io.BytesIO()
    im.save(b, "PNG")
    return media.prepare(b.getvalue())


def wire(monkeypatch, *, bad_first=None, safety_action="proceed", texts=None):
    ok = Verdict(commitment="input_safe_visual", scope="run", status="pass")
    monkeypatch.setattr(
        safety,
        "screen",
        lambda dr: safety.SafetyResult(safety_action, "none", "t", ok, ignored_text=texts or []),
    )
    monkeypatch.setattr(character, "build_card", lambda dr, hero=None, seed="1": (CARD, {}))
    monkeypatch.setattr(
        oath_author, "author", lambda lesson, card: (catalog.core_oath(), {"added": [], "rejected": []})
    )
    monkeypatch.setattr(
        planner,
        "plan",
        lambda lesson, card, age, n=8: ([{"index": i, "setting": "s", "event": "e"} for i in range(1, 9)], {}),
    )
    calls = {"write": 0, "repair": 0}

    def write_scene(**kw):
        calls["write"] += 1
        i = kw["index"]
        if bad_first == i and kw.get("temperature", 0.7) < 0.9:
            return good_page(i, kw["correct_slot"], name="The rabbit"), {}
        return good_page(i, kw["correct_slot"]), {}

    def repair_scene(**kw):
        calls["repair"] += 1
        return good_page(kw["page"].index, kw["correct_slot"]), {}

    monkeypatch.setattr(writer, "write_scene", write_scene)
    monkeypatch.setattr(writer, "repair_scene", repair_scene)
    return calls


def go(drawing, **cfg):
    bus = EventLog()
    run = pipeline.Run(
        cfg=pipeline.RunConfig(lesson_id="sharing", media=False, judge_enabled=False, **cfg),
        drawing=drawing,
        bus=bus,
        story_id="t1",
    )
    pipeline.execute(run)
    return run, bus.all()


def test_happy_path_and_repair(monkeypatch, drawing):
    calls = wire(monkeypatch, bad_first=5)
    run, evs = go(drawing)
    types = [e["type"] for e in evs]
    assert run.outcome == "shipped" and run.error == ""
    assert types.count("scene.accepted") == 8 and "receipt" in types and types[-1] == "run.finished"
    assert calls["repair"] == 1  # page 5 lost the hero's name once, repaired once
    rep = [e for e in evs if e["type"] == "scene.repair"]
    assert rep and rep[0]["data"]["index"] == 5 and "character_named_in_scene" in rep[0]["data"]["failed"]
    r = run.receipt
    assert r["counts"]["shipped_violations"] == 0 and r["counts"]["repairs"] == 1 and "1 pages rewritten" in r["plain"]
    # the correct answer is spread across both slots
    slots = [
        next(i for i, c in enumerate(e["data"]["page"]["choices"]) if c["is_correct"])
        for e in evs
        if e["type"] == "scene.accepted"
    ]
    assert 3 <= slots.count(0) <= 5


def test_unsafe_drawing_refuses_before_any_story(monkeypatch, drawing):
    calls = wire(monkeypatch, safety_action="refuse")
    run, evs = go(drawing)
    types = [e["type"] for e in evs]
    assert run.outcome == "refused" and "run.refused" in types and "character.ready" not in types
    assert calls["write"] == 0 and "receipt" not in types


def test_critical_page_regenerates_once_then_stops(monkeypatch, drawing):
    wire(monkeypatch)

    def always_unsafe(**kw):
        p = good_page(kw["index"], kw["correct_slot"])
        p.scenario = "Benny has a pink bow and a knife."
        return p, {}

    monkeypatch.setattr(writer, "write_scene", always_unsafe)
    run, evs = go(drawing)
    types = [e["type"] for e in evs]
    assert run.outcome == "stopped" and types[-1] == "run.refused"
    assert "scene.accepted" not in types and types.count("scene.repair") == 1


def test_drawing_text_is_never_obeyed(monkeypatch, drawing):
    wire(monkeypatch, texts=["Kill fish"])

    def leaky(**kw):
        p = good_page(kw["index"], kw["correct_slot"])
        if kw["index"] == 2:
            p.scenario = "Benny has a pink bow and wants to kill the fish."
        return p, {}

    monkeypatch.setattr(writer, "write_scene", leaky)
    run, evs = go(drawing)
    crit = [
        e
        for e in evs
        if e["type"] == "verdict"
        and e["data"]["commitment"] == "no_drawing_text_obedience"
        and e["data"]["status"] == "critical"
    ]
    assert crit, "the obedience check must catch the leaked word"


def test_baseline_arm_does_not_repair(monkeypatch, drawing):
    wire(monkeypatch)
    pages = [good_page(i, 1) for i in range(1, 9)]  # always slot 1: position balance fails
    pages[3] = good_page(4, 1, name="The rabbit")
    monkeypatch.setattr(writer, "baseline_story", lambda **kw: (pages, {}))
    run, evs = go(drawing, arm="B0")
    types = [e["type"] for e in evs]
    assert "scene.repair" not in types and run.outcome == "shipped_with_notes"
    broken = {s["commitment"] for s in run.shipped}
    assert {"character_named_in_scene", "correct_choice_position_balanced"} <= broken


def test_writer_tolerates_a_missing_image_prompt_and_retries_bad_json():
    from storybound.clients.errors import ClientError
    from storybound.clients.usage import Result

    good = {"scenario": "Benny hops.", "question": "What now?", "correct": {"text": "Share", "feedback": "Yay"},
            "wrong": {"text": "Keep", "feedback": "Hmm"}}  # fmt: skip
    p = writer.assemble(3, good, 0)
    assert p.image_prompt.startswith("Soft children's-book") and p.choices[0].is_correct

    calls = []

    def call(k):
        calls.append(k)
        return Result(value={"scenario": "x"} if k == 0 else good)

    page, _ = writer._page_from(call, 2, 1)
    assert calls == [0, 1] and page.index == 2 and page.choices[1].is_correct
    with pytest.raises(ClientError):
        writer._page_from(lambda k: Result(value={}), 1, 0)
