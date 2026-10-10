"""Narration: Cloud Text-to-Speech with the Gemini TTS model. Returns audio bytes (mp3) plus timing."""

from __future__ import annotations

import base64
import time

import httpx

from .. import tracing
from ..config import get_settings
from .errors import ClientError
from .gemini import _credentials
from .retry import with_retry
from .usage import Result, Usage, record

URL = "https://texttospeech.googleapis.com/v1/text:synthesize"
_RETRYABLE = {408, 429, 500, 502, 503, 504}


def _token() -> str:
    from google.auth.transport.requests import Request

    c = _credentials()
    if not getattr(c, "valid", False):
        c.refresh(Request())
    return c.token


def _once(text: str, voice: str, model: str, style: str | None) -> tuple[bytes, float]:
    s = get_settings()
    body = {
        "input": {"text": text, **({"prompt": style} if style else {})},
        "voice": {"languageCode": "en-US", "name": voice, "modelName": model},
        "audioConfig": {"audioEncoding": "MP3"},
    }
    t0 = time.time()
    try:
        r = httpx.post(
            URL,
            json=body,
            headers={"Authorization": f"Bearer {_token()}", "x-goog-user-project": s.gcp_project},
            timeout=s.request_timeout_s,
        )
    except httpx.HTTPError as e:
        raise ClientError(f"{type(e).__name__}: {e}", retryable=True) from e
    if r.status_code != 200:
        raise ClientError(r.text[:300], retryable=r.status_code in _RETRYABLE, status=r.status_code)
    return base64.b64decode(r.json()["audioContent"]), round(time.time() - t0, 3)


@tracing.span(kind="TOOL", name="narrate")
def narrate(text: str, *, style: str | None = "Read warmly and slowly to a young child.") -> Result:
    s = get_settings()
    audio, lat = with_retry(lambda: _once(text, s.models.tts_voice, s.models.tts, style))
    usage = Usage(latency_s=lat, model=s.models.tts)
    record(usage, "tts")
    return Result(value=audio, usage=usage)
