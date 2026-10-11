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
