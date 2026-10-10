"""K2 Horizon: the independent judge. OpenAI-compatible; a reasoning model, so give it room and parse tolerantly."""

from __future__ import annotations

import time
from functools import lru_cache

from .. import tracing
from ..config import env, get_settings
from .errors import ClientError, ParseError
from .jsonutil import extract_json
from .retry import with_retry
from .usage import Result, Usage

_RETRYABLE = {408, 429, 500, 502, 503, 504}


@lru_cache
def client():
    from openai import OpenAI

    s = get_settings()
    key = env("IFM_API_KEY")
    if not key:
        raise ClientError("IFM_API_KEY not set")
    return tracing.wrap(OpenAI(api_key=key, base_url=s.ifm_base_url, timeout=s.judge_timeout_s, max_retries=0))


def _once(messages, model: str, max_tokens: int):
    import openai

    t0 = time.time()
    try:
        r = client().chat.completions.create(model=model, messages=messages, temperature=0, max_tokens=max_tokens)
    except openai.APIStatusError as e:
        raise ClientError(str(e)[:300], retryable=e.status_code in _RETRYABLE, status=e.status_code) from e
    except openai.APIError as e:
        raise ClientError(f"{type(e).__name__}: {str(e)[:200]}", retryable=True) from e
    text = (r.choices[0].message.content or "") if r.choices else ""
    u = r.usage
    usage = Usage(
        input_tokens=getattr(u, "prompt_tokens", 0) or 0,
        output_tokens=getattr(u, "completion_tokens", 0) or 0,
        latency_s=round(time.time() - t0, 3),
        model=model,
    )
    return text, usage


def judge_json(system: str, user: str, *, max_tokens: int | None = None) -> Result:
    """Ask the judge for a JSON verdict. One re-ask on unparseable output."""
    s = get_settings()
    model = s.models.judge
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    total = Usage(model=model, calls=0)
    last: ParseError | None = None
    for _ in range(2):
        text, usage = with_retry(lambda: _once(msgs, model, max_tokens or s.judge_max_tokens), attempts=3, base=2.0)
        total = total + usage
        try:
            return Result(value=extract_json(text), usage=total, raw_text=text)
        except ParseError as e:
            last = e
    raise last  # type: ignore[misc]
