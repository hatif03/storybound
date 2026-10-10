from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    latency_s: float = 0.0
    model: str = ""
    calls: int = 1

    def __add__(self, o: Usage) -> Usage:
        return Usage(
            self.input_tokens + o.input_tokens,
            self.output_tokens + o.output_tokens,
            self.latency_s + o.latency_s,
            self.model or o.model,
            self.calls + o.calls,
        )


@dataclass
class Result:
    """What every client returns: parsed payload (or raw text/bytes) plus usage."""

    value: object
    usage: Usage = field(default_factory=Usage)
    raw_text: str = ""
