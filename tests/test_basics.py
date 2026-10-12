import json

import pytest

from storybound import ledger
from storybound.clients.errors import ClientError, ParseError
from storybound.clients.jsonutil import extract_json
from storybound.clients.retry import with_retry
from storybound.config import get_settings


def test_settings_defaults():
    s = get_settings()
    assert s.thresholds.pages == 8 and s.sampling.safety == 1.0
    assert s.models.judge.startswith("IFM/K2")


@pytest.mark.parametrize(
    "text",
    ['{"a": 1}', '```json\n{"a": 1}\n```', '<think>hmm {x}</think>\n{"a": 1}', 'Sure! {"a": 1} done.'],
)
def test_extract_json(text):
    assert extract_json(text) == {"a": 1}


def test_extract_json_fails():
    with pytest.raises(ParseError):
        extract_json("no json here")


def test_retry_only_retryable(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda *_: None)
    n = {"c": 0}

    def flaky():
        n["c"] += 1
        if n["c"] < 3:
            raise ClientError("x", retryable=True)
        return "ok"

    assert with_retry(flaky) == "ok" and n["c"] == 3

    def fatal():
        raise ClientError("bad", retryable=False)

    with pytest.raises(ClientError):
        with_retry(fatal)


def test_ledger_append(tmp_path):
    p = tmp_path / "l.jsonl"
    ledger.append({"run": "r1", "outcome": "ok"}, p)
    ledger.append({"run": "r2"}, p)
    rows = ledger.read(p)
    assert [r["run"] for r in rows] == ["r1", "r2"] and rows[0]["ts_ist"].endswith("+05:30")
    assert json.loads(p.read_text().splitlines()[0])["outcome"] == "ok"


def test_stamp_format():
    s = ledger.stamp("trace")
    assert s.endswith("-IST-trace") and len(s.split("-")[0]) == 8


def test_retry_waits_longer_and_tries_once_more_on_a_quota_error(monkeypatch):
    """HR-007: a Vertex 429 ended runs after three 1 s tries; a per-minute quota needs seconds."""
    sleeps, calls = [], []
    monkeypatch.setattr("storybound.clients.retry.time.sleep", sleeps.append)

    def quota():
        calls.append(1)
        raise ClientError("429 RESOURCE_EXHAUSTED", retryable=True, status=429)

    with pytest.raises(ClientError):
        with_retry(quota, attempts=3, base=1.0)
    assert len(calls) == 4 and all(s >= 4.0 for s in sleeps)  # one extra try, each wait four times longer

    calls.clear(), sleeps.clear()

    def flaky():
        calls.append(1)
        raise ClientError("503", retryable=True, status=503)

    with pytest.raises(ClientError):
        with_retry(flaky, attempts=3, base=1.0)
    assert len(calls) == 3 and sleeps[0] < 2.0  # other errors are unchanged


def test_a_cancelled_vertex_call_is_retried():
    from storybound.clients import gemini

    assert 499 in gemini._RETRYABLE  # "499 CANCELLED" ended a regression job under load (HR-010)


def test_roles_are_routed_by_the_part_of_the_name_before_the_dot(monkeypatch):
    from storybound import config

    monkeypatch.setenv("STORYBOUND_ROUTES", "safety_screen=claude-haiku, scene_writer=nova-2-lite,bad,=x")
    m = config.Models()
    assert m.route("safety_screen.vision") == "claude-haiku"
    assert m.route("scene_writer.3") == "nova-2-lite"
    assert m.route("oath_author") is None and m.routes == {"safety_screen": "claude-haiku", "scene_writer": "nova-2-lite"}


def test_ask_json_uses_the_gateway_for_a_routed_role_and_gemini_otherwise(monkeypatch):
    from storybound.agents import common
    from storybound.clients import gateway, gemini
    from storybound.clients.usage import Result

    seen = []
    monkeypatch.setattr(gateway, "configured", lambda: True)
    monkeypatch.setattr(gateway, "generate_json", lambda user, **kw: seen.append(("gateway", kw["model"])) or Result(value={}))
    monkeypatch.setattr(gemini, "generate_json", lambda user, **kw: seen.append(("gemini", kw.get("model"))) or Result(value={}))
    monkeypatch.setattr(common.get_settings().models, "routes", {"planner": "claude-haiku"})
    common.ask_json("planner.x", "s", "u")
    common.ask_json("writer", "s", "u")
    assert seen == [("gateway", "claude-haiku"), ("gemini", None)]
    monkeypatch.setattr(gateway, "configured", lambda: False)  # no key: fall back to the default model, never fail
    common.ask_json("planner.x", "s", "u")
    assert seen[-1] == ("gemini", None)


def test_gateway_models_are_priced_from_the_gateway_table():
    from storybound.clients.usage import Meter, Usage
    from storybound.config import Prices

    m = Meter()
    m.add(Usage(input_tokens=1_000_000, output_tokens=1_000_000, model="claude-haiku"))
    assert m.cost_usd(Prices()) == 6.6  # 1.1 in + 5.5 out


def test_a_stalled_call_is_sent_a_second_time_and_the_faster_answer_wins():
    import threading
    import time

    from storybound.clients.retry import hedged

    calls = []
    lock = threading.Lock()

    def fn():
        with lock:
            calls.append(1)
            mine = len(calls)
        if mine == 1:
            time.sleep(2.0)  # the stalled request
            return "slow"
        return "fast"

    t0 = time.time()
    assert hedged(fn, after=0.1) == "fast" and len(calls) == 2 and time.time() - t0 < 1.0
    calls.clear()
    assert hedged(lambda: "quick", after=5.0) == "quick"  # no second call when the first answers in time


def test_hedging_waits_for_the_other_call_when_one_fails_and_can_be_switched_off():
    import time

    from storybound.clients.errors import ClientError
    from storybound.clients.retry import hedged

    state = {"n": 0}

    def fn():
        state["n"] += 1
        if state["n"] == 1:
            time.sleep(0.3)
            raise ClientError("504", retryable=True, status=504)
        return "ok"

    assert hedged(fn, after=0.1) == "ok"
    state["n"] = 5
    assert hedged(lambda: "plain", after=0) == "plain"


def test_a_gateway_failure_falls_back_to_gemini_and_is_recorded(monkeypatch):
    from storybound.agents import common
    from storybound.clients import gateway, gemini
    from storybound.clients.errors import ClientError
    from storybound.clients.usage import Result, metered

    def down(user, **kw):
        raise ClientError("503 gateway down", retryable=False, status=503)

    monkeypatch.setattr(gateway, "configured", lambda: True)
    monkeypatch.setattr(gateway, "generate_json", down)
    monkeypatch.setattr(gemini, "generate_json", lambda user, **kw: Result(value={"ok": True}))
    monkeypatch.setattr(common.get_settings().models, "routes", {"planner": "nova-2-lite"})
    with metered() as m:
        assert common.ask_json("planner", "s", "u").value == {"ok": True}
    assert m.fallbacks and m.fallbacks[0]["role"] == "planner" and m.fallbacks[0]["model"] == "nova-2-lite"


def test_an_unknown_gateway_model_is_priced_at_the_dearest_known_one():
    from storybound.clients.usage import Meter, Usage
    from storybound.config import Prices

    m = Meter()
    m.add(Usage(input_tokens=1_000_000, output_tokens=0, model="claude-future"))
    assert m.cost_usd(Prices()) == 5.5  # opus input price, never under-reported


def test_chaos_injects_the_configured_failures_only(monkeypatch):
    import pytest

    from storybound import chaos
    from storybound.clients.errors import ClientError

    monkeypatch.setenv("STORYBOUND_CHAOS", "k2:error:503:1,gemini:stall:0:1,bad,gateway:error:x:1")
    chaos.maybe("gemini")  # a zero-second stall: returns
    chaos.maybe("image")  # not configured: nothing
    with pytest.raises(ClientError) as e:
        chaos.maybe("k2")
    assert e.value.retryable and e.value.status == 503
    assert chaos.active().startswith("k2:error")
    monkeypatch.delenv("STORYBOUND_CHAOS")
    chaos.maybe("k2")  # off by default


def test_the_judge_ensemble_takes_the_stricter_verdict_and_survives_one_judge_failing(monkeypatch):
    from storybound.models import Commitment
    from storybound.oath import judge as j

    c = Commitment(id="p", scope="scene", title="t", plain="p", verifier="judge", rubric="r")

    def fake(items, text, ctx, model=None):
        st = {"k2": "pass", "claude": "violation"}[model or "k2"]
        return {i.id: j.JudgeOut(st, model=model or "k2") for i in items}

    monkeypatch.setattr(j, "judge_batch", fake)
    monkeypatch.setattr(j.get_settings().models, "judge_ensemble", "claude")
    assert j.ensemble_batch([c], "t", {})["p"].status == "violation"  # either judge's violation counts

    def one_down(items, text, ctx, model=None):
        if model == "claude":
            return {i.id: j.JudgeOut("verification_error", model="claude") for i in items}
        return {i.id: j.JudgeOut("pass", model="k2") for i in items}

    monkeypatch.setattr(j, "judge_batch", one_down)
    assert j.ensemble_batch([c], "t", {})["p"].status == "pass"  # the other judge decides
    monkeypatch.setattr(j.get_settings().models, "judge_ensemble", "")
    assert j.ensemble_batch([c], "t", {})["p"].status == "pass"  # no second judge: plain judge_batch


def test_the_ensemble_keeps_an_unverified_safety_promise_unverified_and_ranks_a_warning_above_a_pass(monkeypatch):
    from storybound.models import Commitment
    from storybound.oath import judge as j

    safe = Commitment(id="s", scope="scene", title="t", plain="p", verifier="judge", rubric="r", klass="safety")
    quality = Commitment(id="q", scope="scene", title="t", plain="p", verifier="judge", rubric="r")

    def one_down(items, text, ctx, model=None):
        st = "verification_error" if model == "claude" else "pass"
        return {i.id: j.JudgeOut(st, model=model or "k2") for i in items}

    monkeypatch.setattr(j, "judge_batch", one_down)
    monkeypatch.setattr(j.get_settings().models, "judge_ensemble", "claude")
    out = j.ensemble_batch([safe, quality], "t", {})
    assert out["s"].status == "verification_error"  # a safety check one judge could not run is not a pass
    assert out["q"].status == "pass"  # a quality check falls through to the judge that could

    def warn_second(items, text, ctx, model=None):
        return {i.id: j.JudgeOut("warning" if model == "claude" else "pass", model=model or "k2") for i in items}

    monkeypatch.setattr(j, "judge_batch", warn_second)
    assert j.ensemble_batch([quality], "t", {})["q"].status == "warning"


def test_a_judge_that_failed_is_not_waited_for_again_and_the_fallback_is_listed_once(monkeypatch):
    from storybound.clients import k2
    from storybound.clients.errors import ClientError
    from storybound.clients.usage import Result, metered
    from storybound.models import Commitment
    from storybound.oath import judge as j

    c = Commitment(id="p", scope="scene", title="t", plain="p", verifier="judge", rubric="r")
    primary_calls = []

    def judge_json(system, user, *, max_tokens=None, model=None):
        if model in (None, j.get_settings().models.judge):
            primary_calls.append(1)
            raise ClientError("503", retryable=True, status=503)
        return Result(value={"verdicts": [{"id": "p", "status": "pass", "score": 1.0, "quote": None, "reasoning": "ok"}]})

    monkeypatch.setattr(k2, "judge_json", judge_json)
    monkeypatch.setattr(j.gateway, "configured", lambda: True)
    with metered() as m:
        for _ in range(3):
            assert j.judge_batch([c], "t", {})["p"].status == "pass"
    assert len(primary_calls) == 1 and len(m.fallbacks) == 1


def test_the_writer_only_unwraps_a_known_page_wrapper():
    from storybound.agents import writer

    inner = {"text": "x", "feedback": "y"}
    assert writer.normalise({"page": {"scenario": "s"}}) == {"scenario": "s"}
    assert writer.normalise({"correct": inner}) == {"correct": inner}


def test_a_bad_experiment_setting_does_not_break_the_app(monkeypatch):
    from storybound import config

    monkeypatch.setenv("STORYBOUND_MAX_REPAIRS", "two")
    assert config._env_number("STORYBOUND_MAX_REPAIRS", "2", int) == 2
