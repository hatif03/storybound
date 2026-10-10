"""Unit tests never send traces: an empty key makes tracing a no-op (see storybound.tracing)."""

import os

os.environ["NEATLOGS_API_KEY"] = ""
