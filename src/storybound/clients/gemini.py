"""Gemini on Vertex AI: text, vision and structured JSON. Wrapped so every call is an LLM span."""

from __future__ import annotations

import subprocess
import time
from functools import lru_cache

from .. import tracing
from ..config import get_settings
from .errors import ClientError, ParseError
from .jsonutil import extract_json
from .retry import hedged, with_retry
from .usage import Result, Usage, record

_RETRYABLE = {408, 429, 499, 500, 502, 503, 504}  # 499 CANCELLED: Vertex cancelled the call under load (found by the regression set, HR-008)


def _credentials():
    """ADC if present, else the signed-in gcloud account's token. No key files anywhere."""
    import google.auth
    from google.auth.exceptions import DefaultCredentialsError

    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
    try:
        creds, _ = google.auth.default(scopes=scopes)
        return creds
    except DefaultCredentialsError:
        from google.oauth2.credentials import Credentials

        tok = subprocess.run(
            ["gcloud", "auth", "print-access-token"], capture_output=True, text=True, shell=True, check=True
        ).stdout.strip()
        return Credentials(token=tok)


@lru_cache
def client(timeout_s: float | None = None):
    from google import genai
    from google.genai import types

    s = get_settings()
    c = genai.Client(
        vertexai=True,
        project=s.gcp_project,
        location=s.gcp_location,
        credentials=_credentials(),
        http_options=types.HttpOptions(
            timeout=int((timeout_s or s.request_timeout_s) * 1000), headers={"x-goog-user-project": s.gcp_project}
        ),
    )
    return tracing.wrap(c)


def _usage(resp, model: str, t0: float) -> Usage:
    u = getattr(resp, "usage_metadata", None)
    return Usage(
        input_tokens=getattr(u, "prompt_token_count", 0) or 0,
        # thinking tokens are billed as output tokens but reported separately
        output_tokens=(getattr(u, "candidates_token_count", 0) or 0) + (getattr(u, "thoughts_token_count", 0) or 0),
        latency_s=round(time.time() - t0, 3),
        model=model,
    )


def _call_once(
    model: str, contents, *, system: str | None, json_mode: bool, temperature: float, max_tokens: int, thinking: str
):
    from google.genai import errors, types

    cfg = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_tokens + get_settings().thinking_headroom,  # thinking tokens share this budget
        system_instruction=system,
        response_mime_type="application/json" if json_mode else None,
        thinking_config=types.ThinkingConfig(thinking_level=thinking),
    )
    t0 = time.time()
    try:
        resp = client(get_settings().text_timeout_s).models.generate_content(model=model, contents=contents, config=cfg)
    except errors.APIError as e:
        code = getattr(e, "code", None)
        raise ClientError(str(e)[:300], retryable=code in _RETRYABLE, status=code) from e
    except Exception as e:  # network, timeout
        raise ClientError(f"{type(e).__name__}: {str(e)[:200]}", retryable=True) from e
    text = resp.text or ""
    reason = str(resp.candidates[0].finish_reason) if resp.candidates else ""
    if "MAX_TOKENS" in reason:  # never ship silently truncated output
        raise ClientError(f"output truncated (finish_reason={reason})", retryable=False)
    usage = _usage(resp, model, t0)
    record(usage)
    return resp, text, usage


def _call(model: str, contents, **kw):
    """One model call, hedged: a request that has not answered after `hedge_after_s` is sent a second time (the 87 s stall, HR-011)."""
    return hedged(lambda: _call_once(model, contents, **kw), after=get_settings().hedge_after_s)


def generate(
    prompt: str,
    *,
    model: str | None = None,
    system: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    images: list[tuple[bytes, str]] | None = None,
    thinking: str = "low",
) -> Result:
    """Plain text answer. `images` are (bytes, mime) pairs for vision."""
    from google.genai import types

    model = model or get_settings().models.writer
    parts = [types.Part.from_bytes(data=b, mime_type=m) for b, m in (images or [])] + [prompt]
    _, text, usage = with_retry(
        lambda: _call(
            model,
            parts,
            system=system,
            json_mode=False,
            temperature=temperature,
            max_tokens=max_tokens,
            thinking=thinking,
        )
    )
    return Result(value=text, usage=usage, raw_text=text)


def generate_json(
    prompt: str,
    *,
    model: str | None = None,
    system: str | None = None,
    temperature: float = 0.4,
    max_tokens: int = 4096,
    images: list[tuple[bytes, str]] | None = None,
    thinking: str = "low",
) -> Result:
    """JSON answer, parsed. One re-ask on unparseable output."""
    from google.genai import types

    model = model or get_settings().models.writer
    parts = [types.Part.from_bytes(data=b, mime_type=m) for b, m in (images or [])] + [prompt]
    total = Usage(model=model, calls=0)
    last: ParseError | None = None
    for _i in range(2):
        _, text, usage = with_retry(
            lambda: _call(
                model,
                parts,
                system=system,
                json_mode=True,
                temperature=temperature,
                max_tokens=max_tokens,
                thinking=thinking,
            )
        )
        total = total + usage
        try:
            return Result(value=extract_json(text), usage=total, raw_text=text)
        except ParseError as e:
            last = e
    raise last  # type: ignore[misc]
