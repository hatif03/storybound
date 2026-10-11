# Video generation for Storybound: access, landscape, and a plan

Written Sun 11 Oct 2026 by a research pass. Only `docs/research/video-generation.md` and `evidence/video-gen/` were created; no `src/` or `web/` file was touched. No key appears here. "Not verified" means I could not check it; most web facts below come from secondary pages and are marked as such.

## 0. What we have access to (checked 11 Oct, about 10:30 IST)

| Route | Video or image-to-video? | How I checked | Result |
| --- | --- | --- | --- |
| Vertex AI, project in `config.py`, `us-central1`, gcloud ADC | **Yes.** `veo-2.0-generate-001`, `veo-3.0-generate-001`, `veo-3.0-fast-generate-001`, `veo-3.1-generate-001`, `veo-3.1-fast-generate-001`, `veo-3.1-lite-generate-001` are listed | `genai.Client(vertexai=True).models.list()` (129 models) | Listed is not the same as quota. One real call with the Lite model worked (see 1) |
| Vertex AI, location `global` (what `config.py` uses today) | No Veo models listed (27 models) | same call | Video must use a regional endpoint, `us-central1` worked. Not tried: other regions |
| Hackathon LiteLLM gateway | **No.** 7 models: `nova-micro`, `nova-lite`, `nova-pro`, `nova-2-lite`, `claude-haiku`, `claude-sonnet-4.6`, `claude-opus-4.6` | `GET /models` | No video model. Claude models could act as an independent vision judge for clip frames (image input through the gateway not tested) |
| K2 (`IFM/K2-Horizon-375B-A23B`) | No, text only | `docs/PLATFORMS.md`; not re-listed today | Stays the text judge |
| AWS (hackathon account) | No | CLAUDE.md rule 5 | No Bedrock, so no Nova Reel or Luma on Bedrock |
| Quotas and billing | Not read | I did not open the Vertex quota page or billing console | Actual charge for the test clip: **not verified** |

## 1. The one-clip test (done)

- Model `veo-3.1-lite-generate-001`, `us-central1`, image-to-video from `assets/test-drawings/benign/bunny-bow-carrot.png` (a hackathon sample, not a real child's file), 4 s, 720p, 16:9, `generate_audio=False`, 1 video.
- Result: **success, 43.5 s wall time**, 1 video, 0 filtered by the safety layer. MP4 H.264 1280x720, 4.000 s, **no audio stream** (checked with ffprobe), 778 KB.
- Estimated cost: 4 s x USD 0.05/s = **USD 0.20**, using the Gemini API list price for Lite at 720p (see 2). The Vertex price and any no-audio discount are not verified.
- Files: `evidence/video-gen/bunny-veo31lite-4s.mp4`, `bunny-veo31lite-4s.json` (parameters, latency, estimate, no credentials) and `bunny-veo31lite-4s-frames-0-50-95.png` (frames at 0, 50, 95).
- What I saw by eye, which matters for the oath: colours, bow, carrot and magenta outline were kept, but the **face was redrawn** (lashes, pink cheeks, a new nose), **arms and a leg were added**, the **tail shrank**, and the 4:3 drawing was **pillarboxed** with black bars. The motion is calm and nothing scary. For a child who drew this bunny, "that is not my bunny" is the real risk, and it is exactly what a per-clip hero check should catch.

Not tested: reference images (Lite does not take them), first-and-last frame, clip extension, other Veo models, image-to-video of a drawing that contains a person (see 2, person rules).

## 2. Veo facts (Gemini API docs; Vertex equivalents not verified)

From https://ai.google.dev/gemini-api/docs/veo (fetched today):
- Veo 3.1 durations 4, 6, 8 s; 24 fps; 720p default, 1080p and 4k only at 8 s; Lite has no 4k.
- **Up to 3 reference images** for subject appearance, only on Veo 3.1 standard and Fast, **8 s required**; **Lite does not accept them**.
- First frame (`image`) plus optional `lastFrame`: Veo 3.1 models only.
- Extension: +7 s, up to 20 times, up to 148 s total; not on Lite; 720p only.
- Latency 11 s to 6 min at peak. Every video carries a SynthID watermark. Blocked videos are not charged.
- Image-to-video and reference images: `personGeneration` is `allow_adult` only. How a child's drawing of a child is treated: not tested.
- The page says audio is always generated; on Vertex `generate_audio=False` gave a silent file, so that page is not the whole story.

Prices, USD per second, https://ai.google.dev/gemini-api/docs/pricing (Gemini API, paid tier, video with audio): Veo 3.1 standard 0.40 (720p and 1080p), 0.60 (4k); Fast 0.10 (720p), 0.12 (1080p), 0.30 (4k); **Lite 0.05 (720p), 0.08 (1080p)**. Launch coverage of Lite: https://the-decoder.com/googles-veo-3-1-lite-cuts-video-generation-costs-by-more-than-half/. Vertex's own price page would not render for me; a third-party page quotes a lower video-only tier on Vertex (Lite 0.03/0.05), **not verified**. Runway's official page hosts Veo 3.1 at half price without audio (see 3), a hint that a silent clip may be cheaper; also not verified for Vertex.

## 3. The landscape (what exists, how it keeps characters the same)

Legend: licence / consistency method / clip length / cost / fit for a 4 to 8 year old's own drawing. "nv" = not verified.

### Commercial video models
- **Google Veo 3.1 and Flow.** Veo above. Flow adds "Ingredients" (up to 3 reference images per prompt), "Scenebuilder" (arrange, trim, extend clips) and "Frames to Video" (start and end frame): https://nofilmschool.com/google-flow-ai-filmmaking-tool, https://blog.google/technology/ai/flow-video-tips/ (secondary description; Flow's own docs not read). Consistency: reference images, first/last frame, extend. Clips 4 to 8 s. Cost: see 2. Fit: best for us because we already run on Vertex and use ADC; the weak point is the first-frame-only mode (Lite) drifting, as seen in 1.
- **Runway** (API). Official docs https://docs.dev.runwayml.com/guides/pricing/ : 1 credit = USD 0.01; `gen4_turbo` 5 credits/s (0.05 USD/s), `gen4.5` 12 (0.12), hosted `veo3.1` 40 audio / 20 no audio, `veo3.1_fast` 15 / 10. Max clip length and reference-image features: nv. Fit: a second vendor, but adds a key, a data processor for children's drawings and a new billing line; not needed this weekend.
- **Kling** (Kuaishou). Third-party price snapshots only: Kling 3.0 image-to-video about 0.075 USD/s on a router, official about 0.10 to 0.16 USD/s: https://evolink.ai/blog/kling-3-api-pricing-integration-guide (secondary, sources disagree). Element/reference control is mentioned, how well it works: nv.
- **Luma Ray.** Sources conflict (per-clip 0.30 USD for 5 s at 720p, or about 0.24 USD/s at 1080p): https://wavespeed.ai/blog/cost-and-billing/luma-ai-pricing/. Official page not read.
- **Pika.** Not verified (search returned nothing usable).
- **OpenAI Sora.** Secondary sources say the consumer app ended 26 Apr 2026 and the API was due to end 24 Sep 2026; unconfirmed by OpenAI: https://www.cometapi.com/sora-api-access-in-2026-pricing-rate-limits-and-what-s-actually-available-through-aggregators/. Do not plan on it.

### Open-weight models (all need a GPU we do not have; AWS has EC2 only with a $25 team allowance)
- **Wan 2.2** (Alibaba). Apache 2.0 per the official repo (https://github.com/Wan-Video/Wan2.2). I2V-A14B 480p/720p needs at least 80 GB of GPU memory; TI2V-5B does 720p at 24 fps, "5-second 720P in under 9 minutes" on one 24 GB card (RTX 4090). Clips about 5 s (secondary: https://wan27.org/blog/wan-2-2-longer-than-5-seconds). Consistency: image conditioning; character LoRA is the community's route. Fit: licence is clean; cost and ops are the problem on this account.
- **LTX-Video / LTX-2** (Lightricks). Community open-weights licence: free commercially under USD 10M annual revenue, group-wide, plus restrictions on substitute offerings (secondary summary of https://static.lightricks.com/legal/ltx-2-open-weights-license-0.X.pdf; read the text before use). Clip length and image-to-video limits: nv.
- **HunyuanVideo** (Tencent). Community licence that, per secondary sources, **excludes the EU, UK and South Korea** (https://deepwiki.com/Tencent/HunyuanVideo/5-license-and-legal). A product for families would have to geofence. Poor fit.
- **CogVideoX-5b-I2V** (Zhipu/THUDM). "CogVideoX LICENSE" (terms not read); 6 s, 8 fps, 720x480 only, 5 GB+ VRAM with offload: https://huggingface.co/THUDM/CogVideoX-5b-I2V. Low frame rate and size; fit weak.

### Research pipelines (story to video, multi-agent)
- **MovieAgent** (arXiv 2503.07314; https://github.com/showlab/MovieAgent). Director, screenwriter, storyboard and location-manager agents plan multi-scene films from a script and a "character bank". Model zoo lists SVD and HunyuanVideo-I2V; consistency through per-character ED-LoRA and ROICtrl. Licence not stated on the page. Heavy; needs LoRA training per character.
- **Anim-Director** (arXiv 2408.09787; code under HITsz-TMG). LMM agent writes script and character profiles, makes scene images with consistency prompts, then turns images into video. Licence nv.
- **VideoGen-of-Thought** (arXiv 2412.02259). Training-free: script, keyframes, shot video, smoothing; reports +20.4% face consistency and +17.4% style consistency over baselines (from the NeurIPS 2025 listing, https://neurips.cc/virtual/2025/131787). Code and licence nv.
- **StoryAgent** (arXiv 2411.04925, ICLR 2025 per search). Story designer, storyboard and video agents; LoRA-BE image-to-video for shot consistency. Licence nv.
- **DreamFactory** (arXiv 2408.11788). Multi-agent, "key frames iteration" for cross-scene style and faces; introduces face-distance and style scores, which are the kind of measure our oath could reuse. Licence nv.
- **MAViS** (arXiv 2508.08487) and **MM-StoryAgent** (arXiv 2503.05242, narrated storybook video across text, image and audio): the latter is the closest in shape to Storybound. Licences nv.
- **ComfyUI.** Veo 3.1 and ElevenLabs are available as hosted "partner nodes" (secondary: https://comfyui.org/zh/elevenlabs-is-now-available-in-comfyui). "AI Movie Studio 2" (storyboard, reference-image continuity, timeline; https://comfyui-wiki.com/en/news/2026-09-09-ai-movie-studio-2) is young and its licence is nv.
- Common pattern in all of them: **write script, make keyframe images of the hero first, then animate each keyframe, then stitch.** None of them verifies the result against a promise; that is our gap to fill.

### Children's products (names from search results, none deeply checked)
- **Meta Animated Drawings**, MIT licence (code, weights, dataset) per https://github.com/facebookresearch/AnimatedDrawings. Rigs a human-shaped drawing and plays prerecorded motion. No generative drift, so a child's character cannot change; limited to humanoid figures, so a bunny may not fit. Not tested here.
- **KidsAI Art** (iPad app, sketch to picture or short video; https://apps.apple.com/app/id6784254113), **Storytime AI** (kids' books plus AI read-along videos; https://apps.apple.com/us/app/storytime-ai-story-generator/id6449826316), Kidslox "Kids Drawing Animator" (waitlist only). Licences, models and safety checks: nv. "Storytopia" exists as a Google competition entry for personalised stories without video (https://ai.google.dev/competition/projects/storytopia). I found no product that verifies each clip against stated promises; that is a claim about my search, not about the market.

### What a feature-length story needs (arithmetic, not a vendor claim)
Clips are 4 to 8 s. A 90-minute film is 5,400 s, so about 675 (8 s clips) to 1,350 (4 s clips) clips. One pass at USD 0.05/s is USD 270; at USD 0.40/s it is USD 2,160, before retries (usually several per kept clip). The hard part is not cost but identity across hundreds of shots, which the projects above handle with reference images, key frames or per-character LoRA, and still need human selection. A 3-minute story is 180 s, USD 9 to 72 at those rates.

## 4. Recommended architecture for Storybound

### Principle
Video is an optional upgrade of a page that has **already passed** its image checks. The oath decides whether the child sees the clip; if any clip check fails, the child sees the verified still (plus the existing HyperFrames read-along motion). Nothing unverified is ever shown.

### Pipeline
1. `motion_planner` (agent, cheap text model): reads the verified 8 pages and the budget, picks which pages to animate and writes a motion prompt per page (below).
2. `animate` (tool): Veo image-to-video, **first frame = the verified page illustration** (it already matched the character card at 0.8); for the cover or page 1, the **child's own drawing** is the first frame for the "my drawing woke up" moment. Prompt template: one calm action, "keep the flat crayon style, no text, no new characters, single shot, no camera cuts, slow gentle motion". Lite for first attempts; Veo 3.1 Fast with up to 3 reference images (drawing, character card, the page still) only for the hero page, 8 s, if budget allows (not tested).
3. `clip_verify` (oath): see below.
4. Repair once (regenerate with the failed check named in the prompt), else fall back to the still. Every fallback is listed on the receipt, as budget degradations already are.
5. Assembly: put the passing clips into the existing read-along movie. Whether HyperFrames can embed an MP4 cleanly: not verified; plain `ffmpeg` concat of segments is the fallback (ffmpeg exists on this machine at `C:\ffmpeg`).

### Per-clip commitments (same shape as `docs/DESIGN.md` 3.2)
| Commitment | Verifier | Sampling | On failure |
| --- | --- | --- | --- |
| `clip_present` | ffprobe: decodes, length 4 s +/- 0.3, size, **no audio stream** (child audio stays our own narration) | 1.0 | retry once, then still |
| `clip_single_shot_calm` | deterministic frame differencing on every frame: one scene, no hard cut, no strobe (WCAG three-flashes-per-second rule), bounded motion energy | 1.0 | still |
| `clip_no_text` | OCR or vision pass on 4 to 6 sampled frames; any legible word fails (matches `no_drawing_text_obedience`) | 1.0 | regenerate once, then still |
| `clip_safe_visual` (core) | vision judge on the sampled frames with the real image bytes; fail closed on any error | **1.0, cannot be lowered** | still, critical detection |
| `clip_hero_present` | vision judge: the hero from the character card is visible in at least 3 of 4 frames | 1.0 (cheap) | regenerate once |
| `clip_hero_matches_drawing` | vision judge on first, middle and last frame against the **drawing** and the card's traits list (bow, carrot, colours, number of limbs); pass at 0.8 like `image_matches_card` | 1.0 for the test phase | regenerate once, then still; **the test clip in 1 would likely have failed this** |
| `clip_matches_page` | judge: the action in the page text is visible | 0.5 | regenerate once, then still |

Judge choice: the writer, the pictures and Veo are all Google, so the clip judge should be a different family. K2 is text only, so use `claude-sonnet-4.6` through the LiteLLM gateway for sampled frames (image input via the gateway **not tested**), keep `gemini-3.7-flash` as the cheap first-pass screen. Each judge call is one neatlogs GUARDRAIL span, so the clip story looks like the page story in the trace.

### Keeping the hero the child's
- Anchor on pixels: first frame is the drawing or the verified page, never text alone.
- Use traits from the character card as a checklist and count them before and after (our own test: eyes, nose, limbs and tail changed).
- Prefer short clips (4 s); drift grows with length and with extension chaining (community reports say quality degrades on continuation; secondary).
- Reference images (up to 3, 8 s) are the vendor's tool for identity; they need Veo 3.1 or Fast, so about USD 0.80 to 3.20 per 8 s clip at the listed rates. Not tested.
- If a drawing must never change, use deterministic motion (HyperFrames/GSAP bounce, sway, blink overlays, or Animated Drawings for human shapes). This is the zero-drift option and is what we ship today.

### Choosing pages within a budget
The agent receives `budget_usd` and `deadline_s` (the governor already exists in `config.py`: USD 1.5 and 240 s per story). Rule: the base story costs about USD 0.44 (HANDOFF: about 0.40 plus 0.04 movie), so about USD 1.0 is left. Score pages by (a) an action verb the hero performs, (b) the page where the lesson's correct choice is revealed, (c) the cover, (d) the page's image already passed at a high margin (a safe first frame). Pick the top N such that estimated cost x 1.4 (retry allowance) fits; **degrade order**: drop clips before dropping any safety check, as DESIGN.md already says for judges. Show the choice and cost on the receipt.

### Cost per story (estimates, Gemini API list prices, Vertex not verified)
| Plan | Clips | Veo cost | With 1.4 retry allowance | Plus base 0.44 and clip judges (about 0.05, my guess) |
| --- | --- | --- | --- | --- |
| Lite 720p, 4 s | 1 | 0.20 | 0.28 | about 0.77 |
| Lite 720p, 4 s | 3 | 0.60 | 0.84 | about 1.33 (inside the 1.5 budget) |
| Lite 720p, 4 s | 8 (all pages) | 1.60 | 2.24 | about 2.7 (over budget) |
| Fast 720p, 4 s | 3 | 1.20 | 1.68 | about 2.2 (over budget) |
| Fast 720p, 8 s with references, hero page only | 1 | 0.80 | 1.12 | about 1.6 (slightly over) |

So the budget supports **one to three Lite clips per story**. The cfo.ai model would need a "motion add-on" line (today video is only an unpriced add-on); neatlogs would supply the measured figure, per CLAUDE.md.

## 5. What is feasible before the deadline versus roadmap

Time: today is Sun 11 Oct; code freeze effectively Mon 12 Oct 19:00 IST when the submission window opens; the demo video is not made yet (HANDOFF) and must be at most 3:00.

**Feasible, smallest first (my time guesses, not measured):**
1. (1 to 2 h, no product change) A script that runs the cheap deterministic checks (`clip_present`, `clip_single_shot_calm`) and the two judge checks (`clip_hero_matches_drawing`, `clip_safe_visual`) on the clip we already have, logging to neatlogs and the ledger. It would show the oath catching hero drift with real numbers. Costs well under USD 0.05. This is the best evidence per hour.
2. (half a day) One optional "motion page" behind a flag: cover or page 1 only, Lite, 4 s, repair once, fallback to still, receipt line. Needs edits in `src/` (pipeline, config) which today already carry uncommitted changes; one intent per commit and a ledger run (B0 vs B1) are required by CLAUDE.md. Risk: Veo latency 11 s to 6 min eats the 240 s budget; run it in the background after the story is readable.
3. Rate and quota: unknown; one clip worked, a burst of retries may return 429 like images did.

**Roadmap (do not promise in the demo):**
- Hero reference images on Veo 3.1 Fast; per-child character sheet.
- Page-choosing agent with learned "motion value"; first/last-frame to join pages smoothly.
- Independent clip judge with calibration against a human-labelled set of clips (like `scripts/eval_judge.py` for text): injected faults such as extra limb, text on screen, flash, wrong hero.
- Open-weight route (Wan 2.2 TI2V-5B on a 24 GB GPU) for no data leaving our control; needs a GPU the AWS allowance probably cannot fund.
- Privacy review: a child's drawing goes to a video vendor. Vertex terms for Veo inputs and retention: **not verified**; Gemini API says generated videos are kept 2 days. Real children's drawings must stay out of this path until a parent consents and terms are read (CLAUDE.md rule 3).
- Safety review for ages 4 to 8 beyond frames: no jump scares, no sudden loud sounds (we mute Veo audio), no photorealistic faces, a stricter motion prompt, and a human spot check of the first 50 clips.

**Honest view.** Generative video is a risky fit for "my own drawing comes alive": identity drifts (seen on the first try), clips cost 4 to 20 times what a page picture costs, latency is long, and it adds a data vendor. The oath gives us the right answer to that risk, and the cheapest credible demo is step 1 above plus, if time allows, step 2 on one page. Deterministic motion stays the default.

## 6. Sources checked (fetched 11 Oct 2026)
https://ai.google.dev/gemini-api/docs/veo, https://ai.google.dev/gemini-api/docs/pricing, https://docs.dev.runwayml.com/guides/pricing/, https://github.com/Wan-Video/Wan2.2, https://huggingface.co/THUDM/CogVideoX-5b-I2V, https://github.com/showlab/MovieAgent, https://github.com/facebookresearch/AnimatedDrawings, https://benchlm.ai/md/media-pricing/veo.md, plus the search-result pages linked inline (secondary, summaries only). Vertex's own Veo pages and price page did not render through the fetch tool, so Vertex-specific limits and prices are not verified.
