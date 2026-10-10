"""Oath engine tests: no network. A fake judge stands in for K2."""

from __future__ import annotations

import pytest

from storybound import lessons
from storybound.models import CharacterCard, Choice, Page
from storybound.oath import catalog, engine
from storybound.oath import deterministic as d
from storybound.oath.judge import JudgeOut, check_quote, judge_batch

CARD = CharacterCard(
    name="Benny", species="rabbit", traits=["pink bow on head", "holds an orange carrot", "round tail"]
)


def page(i=1, scenario="Benny the rabbit has one orange carrot.", question="What should Benny do with the carrot?",
         correct_slot=1, **kw) -> Page:  # fmt: skip
    cs = [Choice(id="a", text="Hide it", feedback="Hiding feels lonely.", is_correct=False),
          Choice(id="b", text="Share half with Rosie", feedback="Sharing makes both smile.", is_correct=False)]  # fmt: skip
    cs[correct_slot].is_correct = True
    return Page(index=i, scenario=scenario, question=question, choices=cs,
                image_prompt=kw.pop("image_prompt", "Benny the rabbit with a pink bow holding a carrot"), **kw)  # fmt: skip


def ctx(**kw) -> d.Ctx:
    return d.Ctx(card=CARD, lesson=lessons.get("sharing"), age=6, **kw)


# ---- deterministic ---------------------------------------------------------------------------------------------------


def test_name_missing_is_violation():
    assert d.character_named_in_scene(page(), ctx()).status == "pass"
    bad = page(scenario="The rabbit has one orange carrot.")
    assert d.character_named_in_scene(bad, ctx()).status == "violation"


def test_one_correct_choice():
    p = page()
    assert d.one_correct_choice(p, ctx()).status == "pass"
    p.choices[0].is_correct = True
    assert d.one_correct_choice(p, ctx()).status == "violation"


def test_position_balance():
    pages = [page(i, correct_slot=1) for i in range(1, 9)]
    assert d.correct_choice_position_balanced(pages, ctx()).status == "violation"
    pages = [page(i, correct_slot=i % 2) for i in range(1, 9)]
    assert d.correct_choice_position_balanced(pages, ctx()).status == "pass"


def test_reading_level():
    long = page(
        scenario="Benny the rabbit considered extraordinarily complicated circumstances surrounding the carrot today."
    )
    assert d.age_reading_level(long, ctx()).status == "violation"
    three = page(scenario="Benny sat. Benny sniffed. Benny smiled.")
    assert d.age_reading_level(three, ctx()).status == "violation"
    assert d.age_reading_level(page(), ctx()).status == "pass"


def test_safe_text_whole_words_only():
    assert d.story_safe_text(page(scenario="Benny has a skill for hopping."), ctx()).status == "pass"
    v = d.story_safe_text(page(scenario="Benny will kill the carrot thief."), ctx())
    assert v.status == "critical" and v.matched == "kill"


def test_drawing_text_never_obeyed():
    c = ctx(ignored_text=["Kill fish"])
    assert d.no_drawing_text_obedience([page()], c).status == "pass"
    leaked = page(scenario="Benny wants to kill the fish.")
    r = d.no_drawing_text_obedience([leaked], c)
    assert r.status == "critical" and r.scene == 1
    copied = page(scenario="Benny read the words Kill fish on the wall.")
    assert d.no_drawing_text_obedience([copied], c).status == "critical"


def test_injection_text_tokens():
    c = ctx(ignored_text=["Ignore your rules", "weapons", "fighting"])
    assert d.no_drawing_text_obedience([page()], c).status == "pass"
    assert d.no_drawing_text_obedience([page(scenario="Benny finds weapons.")], c).status == "critical"


def test_repeated_scenarios():
    a = page(1, scenario="Benny finds a big red apple under the old oak tree.")
    b = page(2, scenario="Benny finds a big red apple under the old oak tree today.")
    assert d.no_repeated_scenario([a, b], ctx()).status == "violation"


def test_original_character():
    assert d.original_character_only(CARD, ctx()).status == "pass"
    mouse = CARD.model_copy(update={"name": "Mickey"})
    assert d.original_character_only(mouse, ctx()).status == "violation"


def test_media_checks():
    assert d.illustration_present(None, ctx()).status == "violation"
    assert d.illustration_present(b"\x89PNG\r\n\x1a\n" + b"0" * 5000, ctx()).status == "pass"
    assert d.illustration_present(b"not an image" * 1000, ctx()).status == "violation"
    assert d.narration_present(b"ID3" + b"0" * 4000, ctx()).status == "pass"
    assert d.narration_present(b"", ctx()).status == "violation"


# ---- judge -----------------------------------------------------------------------------------------------------------


def test_quote_check():
    assert check_quote("Share  half", "They Share half of it")
    assert not check_quote("invented line", "They share half of it")


def test_judge_rejects_invented_quote(monkeypatch):
    class R:
        value = {"verdicts": [{"id": "story_safe_text", "status": "critical", "quote": "made up", "reasoning": "x"}]}

        class usage:
            input_tokens = 1
            output_tokens = 1
            latency_s = 0.1

    monkeypatch.setattr("storybound.oath.judge.k2.judge_json", lambda *a, **k: R)
    out = judge_batch([catalog.CORE[2]], "A gentle page about Benny.", {})
    assert out["story_safe_text"].status == "verification_error"


def test_judge_score_decides(monkeypatch):
    class R:
        value = {
            "verdicts": [
                {"id": "lesson_alignment", "status": "pass", "score": 0.5, "quote": "Benny", "reasoning": "weak"}
            ]
        }

        class usage:
            input_tokens = 1
            output_tokens = 1
            latency_s = 0.1

    monkeypatch.setattr("storybound.oath.judge.k2.judge_json", lambda *a, **k: R)
    la = next(c for c in catalog.core_oath().commitments if c.id == "lesson_alignment")
    out = judge_batch([la], "Benny finds a carrot.", {})
    assert out["lesson_alignment"].status == "violation" and out["lesson_alignment"].score == 0.5


# ---- engine ----------------------------------------------------------------------------------------------------------


def fake_judge(status="pass", err=False):
    def fn(items, text, context):
        return {
            c.id: JudgeOut("verification_error", error="down", model="fake")
            if err
            else JudgeOut(status, 0.9, None, "ok", model="fake")
            for c in items
        }

    return fn


def eng(judge=None, **kw) -> engine.Engine:
    return engine.Engine(oath=catalog.core_oath(), ctx=ctx(), judge=judge or fake_judge(), **kw)


def by_id(vs):
    return {v.commitment: v for v in vs}


def test_scene_all_pass():
    vs = by_id(eng().verify_scene(page()))
    assert all(v.ok for v in vs.values()), {k: v.status for k, v in vs.items() if not v.ok}
    assert vs["story_safe_text"].verdict_by == "both" and vs["story_safe_text"].sampled
    assert vs["character_named_in_scene"].verdict_by == "deterministic"


def test_deterministic_failure_skips_judge():
    calls = []

    def spy(items, text, context):
        calls.append([c.id for c in items])
        return {c.id: JudgeOut("pass", model="fake") for c in items}

    bad = page(scenario="Benny will kill the carrot thief.")
    vs = by_id(eng(spy).verify_scene(bad))
    assert vs["story_safe_text"].status == "critical" and vs["story_safe_text"].verdict_by == "deterministic"
    assert all("story_safe_text" not in c for c in calls)


def test_safety_fails_closed_quality_fails_open():
    e = eng(fake_judge(err=True))
    vs = by_id(e.verify_scene(page()))
    assert vs["story_safe_text"].status == "verification_error"
    assert e.gate(vs["story_safe_text"]) == "critical"
    q = vs["correct_choice_teaches_lesson"]
    if q.sampled:
        assert q.status == "warning" and q.judge_status == "verification_error" and e.gate(q) == "accept"


def test_gate_mapping():
    e = eng()
    vs = by_id(e.verify_scene(page(scenario="The rabbit has one carrot.")))
    assert vs["character_named_in_scene"].status == "violation"
    assert e.gate(vs["character_named_in_scene"]) == "repair"


def test_sampling_is_seeded_and_recorded():
    a = engine.sample_draw("7", "x", "scene 1", 0)
    assert a == engine.sample_draw("7", "x", "scene 1", 0) and 0 <= a < 1
    assert a != engine.sample_draw("8", "x", "scene 1", 0)
    e = eng(rates={"quality": 0.0})
    vs = by_id(e.verify_scene(page()))
    assert vs["correct_choice_teaches_lesson"].status == "skipped"
    assert vs["story_safe_text"].sampled  # safety is never lowered


def test_story_scope_and_lesson_alignment():
    pages = [page(i, scenario=f"Benny the rabbit shares item {i} with friend number {i} at spot {i}.", correct_slot=i % 2)
             for i in range(1, 9)]  # fmt: skip
    vs = by_id(eng().verify_story(pages))
    assert vs["schema_valid"].status == "pass" and vs["correct_choice_position_balanced"].status == "pass"
    assert vs["lesson_alignment"].verdict_by == "judge" and vs["lesson_alignment"].status == "pass"


def test_guardrail_verdict_callback():
    seen = []
    eng(on_verdict=seen.append).verify_scene(page())
    assert len(seen) == len([c for c in catalog.CORE if c.scope == "scene"])
    assert all(v.commitment and v.scope == "scene 1" for v in seen)


# ---- oath ------------------------------------------------------------------------------------------------------------


def test_core_cannot_be_removed_or_overridden():
    base = catalog.core_oath()
    o, rej = catalog.merge_additions(
        base,
        [
            {
                "id": "story_safe_text",
                "scope": "scene",
                "rubric": "x" * 30,
            },  # core id: becomes lesson_specific_ prefixed
            {
                "id": "lesson_specific_turns",
                "scope": "scene",
                "title": "Takes turns",
                "rubric": "The hero must take turns with a friend.",
            },
            {"id": "bad", "scope": "run", "rubric": "short"},
        ],
    )
    ids = [c.id for c in o.commitments]
    assert set(catalog.CORE_IDS) <= set(ids)
    assert "lesson_specific_turns" in ids and all(
        not c.core for c in o.commitments if c.id.startswith("lesson_specific_")
    )
    assert rej  # the run-scope addition was rejected
    assert o.hash != base.hash and o.hash == catalog.oath_hash(o.commitments)


def test_oath_hash_is_stable_and_order_independent():
    base = catalog.core_oath()
    rev = list(reversed(base.commitments))
    assert catalog.oath_hash(rev) == base.hash


def test_coverage_reports_gaps():
    cov = engine.coverage(catalog.core_oath())
    assert 0 < cov["pct"] <= 100 and isinstance(cov["uncovered"], list)
    stripped = catalog.core_oath()
    stripped.commitments = [c for c in stripped.commitments if c.id != "narration_present"]
    assert "narrate" in engine.coverage(stripped)["uncovered"]


@pytest.mark.parametrize("scope,n", [("scene", 8), ("story", 4), ("run", 3), ("image", 3), ("audio", 1)])
def test_catalog_scope_counts(scope, n):
    assert len([c for c in catalog.CORE if c.scope == scope]) == n


def test_judge_deferred_while_a_cheap_check_fails():
    calls = []

    def spy(items, text, context):
        calls.append([c.id for c in items])
        return {c.id: JudgeOut("pass", model="fake") for c in items}

    bad = page(scenario="The rabbit has one orange carrot.")  # hero's name missing: deterministic failure
    e = eng(spy)
    e.defer_judge_on_det_fail = True
    vs = by_id(e.verify_scene(bad))
    assert vs["character_named_in_scene"].status == "violation" and not calls
    assert vs["story_safe_text"].status == "pass" and vs["story_safe_text"].verdict_by == "deterministic"
    e.verify_scene(page())  # a clean page is judged
    assert calls
    calls.clear()
    eng(spy).verify_scene(bad)  # observe-only arm: judged regardless
    assert calls
