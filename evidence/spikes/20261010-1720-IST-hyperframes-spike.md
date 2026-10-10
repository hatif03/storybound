# HyperFrames spike (10 Oct 2026, 17:00-17:20 IST)

Question: can we use the open-source [HyperFrames](https://github.com/heygen-com/hyperframes) renderer (Apache-2.0, npm `hyperframes` 0.8.145) as the render and technical-check layer of the video harness, and keep only our own layer (claim sourcing, video oath, repair, receipt, tracing) on top?

Setup: scratch folder outside the repo, `npm i hyperframes`, telemetry disabled (`hyperframes telemetry disable`, `DO_NOT_TRACK=1`), `HYPERFRAMES_SKIP_SKILLS=1`. Machine: Windows 11, Node 24.20, system Chrome, ffmpeg 2025-08, Intel Iris Xe (hardware capture). Test composition: [hyperframes/index.html](hyperframes/index.html) (8 s: animated title, a claim number, three bars, one 7 s voice-over clip). No child drawings used.

| Test | Result |
| --- | --- |
| `hyperframes check` on the good composition | passed: lint 0 errors (3 warnings: elements without ids), runtime 0, layout 0 issues in 9 samples, motion 0, contrast 24/24 text checks pass WCAG AA |
| Determinism: render the same composition twice | **byte-identical**: both files 522,254 bytes, SHA-256 `0f24b936f75c328640bcf428e07a09ab06c9f9bcf8e2f6c5738621866c24ed55` (one machine, one run each; not tested across machines) |
| Render speed | 8 s video in 18.5 s and 16.8 s of render time (about 2x real time) |
| Broken: reference to a missing image | caught by lint (`missing_local_asset`), exit "Check failed". It also states "Browser session never ran: layout, motion and contrast are empty placeholders, not a clean pass", so a lint error hides the browser checks until fixed |
| Broken: text wider than the canvas | caught by layout check at every sampled time from 1.1 s on |
| Broken: low-contrast text | caught: `#claimlabel 1.11:1 (need 3:1)`, with a suggested colour |
| Broken: script error in the page | caught by the runtime check (`nothere is not defined`) |

Other findings:
- The CLI also has `inspect`, `snapshot`, `validate`, `normalize-audio` (loudness by LUFS), `compare`, `benchmark`, local `tts` (Kokoro) and `transcribe` (whisper-cpp, not installed here). These overlap the technical half of our planned video oath.
- It fetches Google Fonts on first use (cached afterwards) and the template loads GSAP from a CDN: vendor GSAP and fonts locally for an offline, reproducible render.
- `publish`, `cloud` rendering and `auth` send content to HeyGen's services: **we do not use them**. `init` contacts GitHub to check skills unless `HYPERFRAMES_SKIP_SKILLS=1`.
- Docker is installed but not running; not needed.

Decision: adopt HyperFrames for rendering and the layout, contrast, asset and runtime checks. Our harness adds what it does not check: every on-screen number resolves to an evidence file, the three tools each cover the five points, no child data or secrets, the receipt, the repair loop and the neatlogs trace. Not yet tested: a real scene with images and several audio clips; the HyperFrames agent skills (not installed).
