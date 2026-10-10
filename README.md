# Storybound

A story agent that keeps its promises. A child's drawing and a lesson go in; the agent writes an oath, checks every page against it before the child sees it, repairs pages that break it, and ships a receipt.

Built for neatHack (10-12 Oct 2026) with neatlogs, Entire and cfo.ai. Work in progress: see `hackathon.md` for the build log, `docs/DESIGN.md` for the design, `docs/API.md` for the HTTP contract and `docs/PLATFORMS.md` for the state of every platform.

The code here is written during the hackathon window.

## Run it (development)

```powershell
uv sync                      # creates .venv from pyproject.toml
copy .env.example .env       # then fill in the keys; never commit .env
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe scripts\spikes\spike_m1.py     # one traced call per integration
```
Google credentials come from `gcloud auth application-default login` (or the signed-in gcloud account).

## Key deliverables and where to find them
Filled in as the build progresses (`EVIDENCE.md` will be generated from `evidence/`).
