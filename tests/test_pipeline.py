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


def fake_quiz(pages, card, lesson, age, seed, bad_quote_on=None):
    from storybound.models import Quiz, QuizItem, QuizOption

    items = []
    for i, p in enumerate(pages[:4], 1):
        quote = "this line is not on the page at all" if i == bad_quote_on else " ".join(p.scenario.split()[:5])
        items.append(QuizItem(index=i, kind=("recall", "order", "feeling", "lesson")[i - 1], question=f"What did {card.name} do?",
                              options=[QuizOption(id="a", text="Shared", is_correct=True), QuizOption(id="b", text="Hid", is_correct=False),
                                       QuizOption(id="c", text="Ran", is_correct=False)],
                              evidence_page=p.index, evidence_quote=quote, explain="Look: the line."))  # fmt: skip
    return Quiz(items=items, talk_about="Who do you like to share with?")


def wire(monkeypatch, *, bad_first=None, safety_action="proceed", texts=None):
    monkeypatch.setattr(pipeline.quizmaker, "make_quiz", fake_quiz)

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


def test_failed_review_rolls_back_pages_written_ahead(monkeypatch, drawing):
    """Pages are written while earlier ones are under review; a failed review discards everything after it."""
    from storybound.oath.judge import JudgeOut

    wire(monkeypatch)
    writes = []
    orig_write = writer.write_scene

    def spy_write(**kw):
        writes.append(kw["index"])
        return orig_write(**kw)

    monkeypatch.setattr(writer, "write_scene", spy_write)
    seen = {}

    def judge(items, text, context):
        page = int(text.split()[1]) if text.startswith("PAGE") else 0  # "PAGE n"
        seen[page] = seen.get(page, 0) + 1
        out = {}
        for c in items:
            if page == 3 and seen[page] == 1 and c.id == "correct_choice_teaches_lesson":
                out[c.id] = JudgeOut("violation", None, "x", "the right answer does not teach the lesson", model="fake")
            else:
                out[c.id] = JudgeOut("pass", 0.9, None, "ok", model="fake")
        return out

    bus = EventLog()
    run = pipeline.Run(
        cfg=pipeline.RunConfig(lesson_id="sharing", media=False, judge_fn=judge),
        drawing=drawing, bus=bus, story_id="t2",
    )  # fmt: skip
    pipeline.execute(run)
    evs = bus.all()
    accepted = [e["data"]["index"] for e in evs if e["type"] == "scene.accepted"]
    assert accepted == list(range(1, 9)), (
        f"pages are shown in order, each exactly once: {run.error} {[e['type'] for e in evs][-6:]}"
    )
    assert run.outcome == "shipped" and run.error == ""
    assert seen[3] == 2, "page 3 was reviewed, failed, repaired and reviewed again"
    assert writes.count(4) >= 2, "page 4 was written ahead, discarded after the rollback, and written again"
    rep = [e for e in evs if e["type"] == "scene.repair"]
    assert rep and rep[0]["data"]["index"] == 3
    # nothing is shown before its review has come back: page 3 is accepted only after the repair
    first3 = next(i for i, e in enumerate(evs) if e["type"] == "scene.accepted" and e["data"]["index"] == 3)
    repair = next(i for i, e in enumerate(evs) if e["type"] == "scene.repair")
    assert repair < first3


def test_receipt_lists_each_promise_and_gate_rewrites_are_resent(monkeypatch, drawing):
    wire(monkeypatch)
    # all pages put the correct answer in slot 1: the story gate must reorder some, and say so
    monkeypatch.setattr(writer, "write_scene", lambda **kw: (good_page(kw["index"], 1), {}))
    run, evs = go(drawing)
    revised = [e for e in evs if e["type"] == "scene.accepted" and e["data"].get("revised")]
    assert revised, "pages reordered by the story gate are sent again"
    promises = run.receipt["promises"]
    assert len(promises) == len(catalog.with_quiz(catalog.core_oath()).commitments)
    assert {p["status"] for p in promises} <= {"kept", "broken", "not_checked"}
    assert next(p for p in promises if p["id"] == "correct_choice_position_balanced")["status"] == "kept"


def test_self_critique_arm_observes_without_repairing(monkeypatch, drawing):
    wire(monkeypatch)
    pages = [good_page(i, 1) for i in range(1, 9)]
    monkeypatch.setattr(writer, "baseline_story", lambda **kw: (pages, {}))
    called = []
    monkeypatch.setattr(writer, "self_critique", lambda p, **kw: called.append(1) or p)
    run, evs = go(drawing, arm="B2")
    assert called and "scene.repair" not in [e["type"] for e in evs]
    assert "correct_choice_position_balanced" in {s["commitment"] for s in run.shipped}


def test_quiz_questions_that_fail_a_promise_are_dropped_not_shown(monkeypatch, drawing):
    wire(monkeypatch)
    monkeypatch.setattr(pipeline.quizmaker, "make_quiz", lambda *a, **kw: fake_quiz(*a, bad_quote_on=2, **kw))

    def broken_repair(q, failures, pages, age, seed):
        return q  # the repair does not fix it

    monkeypatch.setattr(pipeline.quizmaker, "repair_item", broken_repair)
    run, evs = go(drawing)
    ready = [e for e in evs if e["type"] == "quiz.ready"]
    assert ready and [i["index"] for i in ready[0]["data"]["items"]] == [1, 3, 4]
    assert any(v.commitment == "quiz_quote_in_story" and v.status == "violation" for v in run.verdicts)
    assert run.outcome == "shipped" and run.shipped == []


def test_quiz_is_only_for_the_gated_arm(monkeypatch, drawing):
    wire(monkeypatch)
    pages = [good_page(i, 1) for i in range(1, 9)]
    monkeypatch.setattr(writer, "baseline_story", lambda **kw: (pages, {}))
    run, evs = go(drawing, arm="B0")
    assert not [e for e in evs if e["type"] == "quiz.ready"]
