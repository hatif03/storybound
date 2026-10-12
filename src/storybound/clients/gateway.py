"""The hackathon LiteLLM gateway (Claude and Nova models) as a second model provider for any agent role, text or vision.

OpenAI-compatible; the same client K2's judge uses (`k2.client(gateway=True)`), so every call is a neatlogs LLM span with tokens and latency.
A role is routed here when its model name starts with `claude` or `nova` (see `Models.route`). Key and base URL come from `.env`.
"""

from __future__ import annotations

import base64
import time

from .errors import ClientError, ParseError
from .jsonutil import extract_json
from .k2 import _RETRYABLE, client
from .retry import with_retry
from .usage import Result, Usage, record

GATEWAY_PREFIXES = ("claude", "nova")


def is_gateway(model: str | None) -> bool:
    return bool(model) and model.startswith(GATEWAY_PREFIXES)


def _content(prompt: str, images: list[tuple[bytes, str]] | None):
    if not images:
        return prompt
    parts: list[dict] = [{"type": "text", "text": prompt}]
    for data, mime in images:
        parts.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{base64.b64encode(data).decode()}"}})
    return parts


def _once(messages, model: str, temperature: float, max_tokens: int):
    import openai

    from .. import chaos

    chaos.maybe("gateway")

    t0 = time.time()
    try:
        r = client(True).chat.completions.create(model=model, messages=messages, temperature=temperature, max_tokens=max_tokens)
    except openai.APIStatusError as e:
        raise ClientError(str(e)[:300], retryable=e.status_code in _RETRYABLE, status=e.status_code) from e
    except openai.APIError as e:
        raise ClientError(f"{type(e).__name__}: {str(e)[:200]}", retryable=True) from e
    text = (r.choices[0].message.content or "") if r.choices else ""
    if r.choices and r.choices[0].finish_reason == "length":
        raise ClientError("output truncated (finish_reason=length)", retryable=False)
    u = r.usage
    usage = Usage(
        input_tokens=getattr(u, "prompt_tokens", 0) or 0,
        output_tokens=getattr(u, "completion_tokens", 0) or 0,
        latency_s=round(time.time() - t0, 3),
        model=model,
    )
    record(usage)
    return text, usage


def generate_json(
    prompt: str,
    *,
    model: str,
    system: str | None = None,
    temperature: float = 0.4,
    max_tokens: int = 2048,
    images: list[tuple[bytes, str]] | None = None,
) -> Result:
    """JSON answer from a gateway model, parsed. One re-ask on unparseable output (same contract as `gemini.generate_json`)."""
    msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": _content(prompt, images)}]
    total = Usage(model=model, calls=0)
    last: ParseError | None = None
    for _ in range(2):
        text, usage = with_retry(lambda: _once(msgs, model, min(temperature, 1.0), max_tokens), attempts=3, base=2.0)
        total = total + usage
        try:
            return Result(value=extract_json(text), usage=total, raw_text=text)
        except ParseError as e:
            last = e
    raise last  # type: ignore[misc]


def configured() -> bool:
    """The gateway can be used only when its key and address are present."""
    from ..config import env

    return bool(env("LITELLM_API_KEY") and env("LITELLM_BASE_URL"))


__all__ = ["GATEWAY_PREFIXES", "configured", "generate_json", "is_gateway"]
