"""Illustrations: Gemini image models on Vertex. Returns PNG/JPEG bytes."""

from __future__ import annotations

import time

from .. import tracing
from ..config import get_settings
from .errors import ClientError
from .gemini import client
from .retry import with_retry
from .usage import Result, Usage, record

_RETRYABLE = {408, 429, 500, 502, 503, 504}


def _once(model: str, prompt: str, ref: tuple[bytes, str] | None) -> tuple[bytes, str, Usage]:
    from .. import chaos

    chaos.maybe("image")
    from google.genai import errors, types

    parts = ([types.Part.from_bytes(data=ref[0], mime_type=ref[1])] if ref else []) + [prompt]
    cfg = types.GenerateContentConfig(response_modalities=["IMAGE"])
    t0 = time.time()
    try:
        resp = client().models.generate_content(model=model, contents=parts, config=cfg)
    except errors.APIError as e:
        code = getattr(e, "code", None)
        raise ClientError(str(e)[:300], retryable=code in _RETRYABLE, status=code) from e
    except Exception as e:
        raise ClientError(f"{type(e).__name__}: {str(e)[:200]}", retryable=True) from e
    for cand in resp.candidates or []:
        for p in (cand.content.parts if cand.content else []) or []:
            if getattr(p, "inline_data", None) and p.inline_data.data:
                u = resp.usage_metadata
                usage = Usage(
                    input_tokens=getattr(u, "prompt_token_count", 0) or 0,
                    output_tokens=getattr(u, "candidates_token_count", 0) or 0,
                    latency_s=round(time.time() - t0, 3),
                    model=model,
                )
                return p.inline_data.data, p.inline_data.mime_type or "image/png", usage
    raise ClientError("no image in response", retryable=True)


@tracing.span(kind="TOOL", name="illustrate")
def illustrate(prompt: str, *, reference: tuple[bytes, str] | None = None) -> Result:
    """Primary model, then the fallback model once. `reference` is the child's drawing."""
    s = get_settings()
    try:
        data, mime, usage = with_retry(lambda: _once(s.models.image, prompt, reference), attempts=3, base=6.0)
    except ClientError:
        data, mime, usage = with_retry(lambda: _once(s.models.image_fallback, prompt, reference), attempts=3, base=6.0)
    record(usage, "image")
    return Result(value=data, usage=usage, raw_text=mime)
