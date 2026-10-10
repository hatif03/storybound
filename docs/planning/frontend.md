# Storybound — frontend design plan

Written 9 October 2026. Companion to [plan.md](plan.md) and [pitch.md](pitch.md); the asset shopping list is [assets.md](assets.md). No code. This file decides what the child sees, hears and touches, on a phone, a tablet and a desktop, and why.

Research basis: NN/g on children's physical development and touch targets, the MTAGIC touch study (Anthony et al., IJHCS 2019), Google's "building for kids" guidance, the Cooney Center / Sesame preschool-tablet practices, the UK ICO Children's Code age bands, the Radesky et al. 2022 study of manipulative design in apps for 3–5-year-olds, the UC Irvine enhanced-ebook study, Katzir et al. 2013 on font size, WCAG 2.2, Apple's Kids Category rules, and the FTC's COPPA guidance and 2025 amendments. Where a rule is my inference rather than a finding, it says **(inference)**. Several primary sources (the full NN/g report, PBS Kids and Common Sense design principles) were paywalled or not found; the gaps are listed in §13. **Test with a real 4–8-year-old on a real device**: published touch-size studies cover ages 5–10 on specific hardware.

## 1. Who it is for, and what that decides

The primary user is a **4–8-year-old**, and the range is wide.

| Age | What they can do | What follows |
| --- | --- | --- |
| 4–5 | Tap, simple swipe, scribble-draw. Mostly cannot read. Drag is hard; pinch and rotate are not realistic. Cannot do two-handed gestures | Every action has a **picture and a voice**. One big tap per decision |
| 6 | Simple clicks, short drags. England's Year 1 phonics check: 80% met the standard in 2025, so about 1 in 5 cannot reliably decode | Text is an **optional layer**, never the only cue |
| 7–8 | Reads short sentences, draws with intent, handles a mouse or trackpad (trackpads are preferred to mice) | Text on by default but short; a mouse works but is not required |

The secondary user is a **parent or teacher**: they set up, supervise, and read the receipt. Their area is separate, gated and calm. A third audience, the **hackathon judge**, sees the parent's receipt plus a "for builders" panel in it ([§9](#9-the-parent-area-and-the-receipt)).

Design stance in one line: **a paper-craft storybook world, where the child's own drawing is the hero, a small guide voices everything, nothing can be lost or lost at, and every promise the agent keeps shows up as a sticker.**

## 2. Principles, each tied to its source

1. **Usable without reading.** Every control has an icon and a voice; text supports, never carries alone. *ICO Annex B (text "of very limited use" 0–5); Google; phonics data.*
2. **Big targets.** Child-facing primary targets are **≥ 20 mm (~76 CSS px); use 80 px**, with an invisible hit area enlarged a further ~12 px and generous spacing. Adult minimums (44 pt / 48 dp) apply only to the parent area. *NN/g: 2 cm × 2 cm; Anthony 2019 (children miss small targets; enlarge the active area beyond the widget).*
3. **Tap, swipe and draw only.** No pinch, rotate, double-tap, long-press (except the parent gate) or precise drag for the child. Any drag has a tap alternative. *NN/g; Google; Anthony 2019 review.*
4. **Keep controls off the bottom edge and away from screen borders.** Preschoolers rest their wrists on the bottom of a landscape tablet and trigger edge hotspots. *Cooney Center; Anthony 2019.*
5. **Instant, obvious feedback on every touch**, and debounce repeat touches ("holdover" taps). *Anthony 2019.*
6. **Two choices, each read aloud, each with a picture.** *Google (do not rely on text alone). Two options is **(inference)**.*
7. **No wrong answers, no scores, no loss framing.** A "try again" is a warm voice plus a visual hint; glowing or pulsing alone did not help ages 2–5, so pair it with motion or voice. *Google; Hiniker 2015 via Anthony; Radesky 2022.*
8. **No dark patterns:** no timers, streaks, nagging characters, "come back tomorrow", autoplay chains, ads, external links, chat, purchases. *Radesky 2022 (about 4 in 5 apps used manipulative design); Apple 1.3 and 5.1.4; FTC dark-patterns statement.*
9. **Extras serve the story.** Animation and sound that are unrelated to the narrative are cut; they reduce story recall in 3–5-year-olds. *UC Irvine / Cooney Center.*
10. **Colour for delight, luminance for legibility; never colour alone for meaning.** Children prefer saturated colours but saturation did not improve their performance. About 8% of boys have a colour-vision deficiency, mostly red–green. *Buckingham & Harrower; CVD prevalence studies.*
11. **Text sized and spaced for early readers:** larger and wider-spaced, left-aligned, no italics, short. *Katzir 2013 (smaller font hurt 2nd-grade comprehension); Hughes & Wilkins (word spacing); BDA guidance. Values are **(inference)**.*
12. **The drawing is personal data.** Collect the minimum, keep it only for the session unless a parent opts in, delete on request, no profiling, no third-party scripts or analytics in the child experience, **self-host fonts and assets** (a font CDN call sends the child's IP to a third party). *Apple 5.1.4 (drawings listed as potentially personal information); COPPA FAQ and the 2025 amendments; UK AADC data minimisation.*
13. **Honest by construction.** The child never sees a sticker for a promise that was not kept; the parent's receipt shows everything. A story is never presented as checked when it was not ([pitch.md §3](pitch.md#3-the-story-the-long-version)).

## 3. Concept and art direction

**World.** A warm paper desk with a storybook on it, drawn in the **bright flat-vector cartoon style** of the supplied scenes, cards and stickers: clean shapes, warm colours, simple backgrounds. The child's drawing is pasted into the story as the hero's "reference sticker", so every page is visibly *theirs*.

**Guide.** A brown owl with a blue bow tie called **Pip** (working name), supplied as a Rive file with **15 expressions** ([assets/README.md](assets/README.md) maps each to a screen: happy for Welcome, wink for ready, sunglasses for a kind choice, dizzy for "let's think", bubble-blowing for the wait, cake and balloons for the end; the crying and angry owls are never shown to a child). Pip: greets, reads UI prompts aloud, and consoles on a refusal (the shy owl). Pip never nags, never talks about time, never says "wrong". Poses we lack (paint, stamp, hug, point, read) are done with a prop overlay or added in Rive. Khan Academy Kids uses a mascot guide the same way; Toca Boca and Sago Mini avoid scores and text instructions; Endless Alphabet lets every touch speak.

**The promise as a picture.** The oath becomes a **sticker sheet** the child earns as pages pass their checks: a shield-star (kind and safe), a name-tag (the hero's name on every page), a check (one right answer), a heart-book (the lesson), a palette (pictures look like the hero), a speaker (reading aloud works). The sheet is the child-sized face of the receipt, and a moment of delight at the end.

**Illustration style for generated art** (a single style prompt prefix kept in config and in the guardrail for `visual_trait_referenced`): "bright flat-vector storybook illustration, soft rounded shapes, clean edges, warm colours, simple background, the hero clearly in the centre, no text in the image" (chosen to match the supplied placeholder scenes, so generated pictures and stock art do not clash). Backgrounds are simple on purpose: it keeps the hero consistent and the page calm.

**Mood words:** warm, tactile, rounded, sunlit, slow. Not: neon, glossy, busy, loud.

**What we keep from Storytopia's look, and what we do not.** Kept as ideas: an orange brand warmth, crayon swatches for colour choice, a watercolour tree-and-grass border, a tablet-first storybook card with the picture up top and two choice buttons below, progress dots. Changed: bigger targets, no text-only buttons, a guide, randomised choice order (their correct answer was always the first button), voice on everything, no mobile caveat ("best viewed on desktop or iPad").

## 4. Visual system

### 4.1 Colour tokens

Names are CSS custom properties. Contrast is for the stated pairing; verify with a checker before freezing.

| Token | Value | Use | Pairing and contrast |
| --- | --- | --- | --- |
| `--paper` | `#FFF8EA` | Page background | with `--ink`: ≥ 12:1 |
| `--paper-2` | `#FDEFD3` | Cards, book page | with `--ink`: ≥ 10:1 |
| `--ink` | `#2A2745` | Text, outlines | on `--paper`: AAA |
| `--sun` | `#FFC93C` | Primary button fill | `--ink` text: ≥ 9:1. Never white text |
| `--sky` | `#59B8F3` | Secondary, drawing | `--ink` text |
| `--leaf` | `#6CC57A` | Success, "kept" | `--ink` text; always with a star icon |
| `--berry` | `#FF7096` | Accent, hearts | `--ink` text |
| `--tangerine` | `#FF9A3C` | Brand warm (nods to Storytopia) | `--ink` text |
| `--grape` | `#8F73E0` | "Let's think" feedback | `--ink` text, or white on a dark grape |
| `--cloud` | `#E9E4F5` | Disabled, quiet panels | |
| `--shadow` | ink at 18% | Sticker shadow | |

Rules: feedback for a "not that one" choice is **grape plus a thought-bubble icon**, never red, never an X. Success is **leaf plus a star**. Colour is always doubled by shape and position. Text on a photo or illustration sits on a `--paper-2` plate, not directly on the picture.

**Drawing palette (colour-blind-safe and kid-friendly).** Start from the Okabe–Ito set, then add what children actually need: black `#222`, orange `#E69F00`, sky blue `#56B4E9`, bluish-green `#009E73`, yellow `#F0E442`, blue `#0072B2`, vermillion `#D55E00`, reddish-purple `#CC79A7`, plus brown `#8A5A2B`, pink `#FF9EC0`, and an eraser. Ten colours plus the eraser on two rows. Each crayon is a big crayon-shaped target; colours are identifiable by **position** as well as hue, and the chosen one is shown by a lifted crayon and a thick ring, not by colour alone.

### 4.2 Typography

| Role | Font | Why | Size (rem, fluid) |
| --- | --- | --- | --- |
| Story text | **Andika** (SIL OFL) | Designed for beginning readers: single-storey a and g, distinguishable b/d/p/q and I/l/1 | `clamp(1.75rem, 1.2rem + 2.2vw, 2.5rem)`; line-height 1.55; letter-spacing 0.02em; word-spacing 0.1em; left-aligned; no italics; ≤ ~36 characters per line; 1–2 short sentences per page |
| Buttons, headings, Pip's words | **Fredoka** (SIL OFL) | Rounded, friendly, bold; display use only, not paragraphs | `clamp(1.5rem, 1.1rem + 1.6vw, 2.25rem)` |
| Parent area and receipt | **Atkinson Hyperlegible** (Braille Institute, OFL-style) | Designed for legibility; quiet next to the child world | 1–1.125rem, line-height 1.5 |
| Numbers on the receipt | Atkinson with tabular figures | Aligned columns | |

Notes: a small study suggests Lexend helps reading, but I found no independent replication; and there is no evidence for dyslexia-specific typefaces (OpenDyslexic). So: Andika for the reading, spacing for comfort, and a parent setting for **text size (small, medium, large)** and **text on/off**. Comic Neue has a double-storey a and is not used for reading. All fonts are **self-hosted as WOFF2**, subset to Latin, `font-display: swap`, no external requests.

### 4.3 Shape, depth, motion

- Corner radius 28–40 px for cards and buttons; fully round for icon buttons. Thick outlines: 4 px `--ink`.
- "Sticker" depth: a hard offset shadow (0 6 px, no blur) that collapses on press (the button visibly pushes down, ≤ 120 ms). It is the instant feedback.
- Paper-grain overlay at 4–6% opacity on `--paper`; a slight rotation (±1°) on cards so the UI feels placed by hand.
- Motion is springy and short (≤ 300 ms); one idea moves at a time; page turns slide with a soft paper curl. With `prefers-reduced-motion`: crossfades only, Pip's idle loop stops, confetti becomes a static sticker burst.

### 4.4 Sound

Narration is the primary audio; everything else sits underneath it.

| Layer | Behaviour |
| --- | --- |
| Narration | Neural TTS, a warm voice at ~0.9× speed. Pre-rendered for UI lines (Pip) and generated per story for pages and choices |
| UI sounds | Soft pop on tap, paper rustle on page turn, a rising chime on a kept promise, a gentle "boop" on a choice. Short (≤ 400 ms), quiet, no harsh transients |
| Music | A very quiet loop, **off by default**, volume capped, ducked under narration |
| Controls | An always-visible speaker icon (mute / unmute) and a volume slider in the parent area; never assume sound is on, so every voiced fact also has a picture |
| Formats | **MP3 or AAC**, not OGG or WebM Opus (unreliable in Safari). Short SFX decoded once with Web Audio and played from an audio sprite; narration and music through `<audio>`. Re-resume the context after interruptions (calls, alarms) and test with the iPhone silent switch on |
| iOS | The first screen's big **"Let's go!"** button is the audio unlock: create or resume one `AudioContext` inside that tap, reuse it, and re-unlock after `visibilitychange`. Test on a real iPhone and iPad |

## 5. Responsive layout

Mobile-first, but **tablet landscape is the reference device**: preschoolers usually hold tablets in landscape, and Storytopia was built for it.

| Class | Width | Layout notes |
| --- | --- | --- |
| Phone portrait | ≤ 600 px | One page at a time: picture on top (4:3), text plate under it, choices stacked, Pip as a small corner helper. Page arrows are large side buttons at **mid-height**, not at the bottom |
| Phone landscape | ≤ 900 px wide, short height | Picture left, text and choices right; Pip hidden except on pauses |
| Tablet portrait | 601–900 px | Like phone portrait with bigger type and a side stepping-stone path |
| **Tablet landscape** | 901–1279 px | **Two-page spread:** picture on the left page, text and choices on the right page; stepping stones along the top; bottom 14% kept free of controls (wrist rest) |
| Desktop | ≥ 1280 px | The same spread, centred in a book of max ~1200 px with a paper desk around it; mouse hover states; keyboard focus rings; arrow keys turn pages |

Details:

- **Fluid sizing** with `clamp()` and `rem`; respect browser zoom; no fixed pixel heights on text areas.
- **Safe areas:** `env(safe-area-inset-*)`; no controls under notches.
- **Hit areas:** every control ≥ 80 px with the enlarged invisible area; a minimum 16 px gap between targets.
- **Orientation:** works in both; a spread on landscape, a single page on portrait; no forced rotation prompt.
- **Image ratio:** generate one master at **4:3** with the hero inside the middle 80% (works for portrait stacks and landscape spreads, and crops safely to 3:2). Allowed sizes depend on the image model, so spike S1 confirms; fallback 3:2 with a crop.
- **Performance:** preload the next page's image and audio; WebP/AVIF; scene images ≤ ~250 KB on mobile; lazy-load the rest; the first page appears while later ones are still being generated (Storytopia's 4-then-4 idea, driven by the real graph).
- **Input:** pointer events for drawing (check `pointerType` and contact size, ignore large palm contacts); touch, mouse and stylus work; no hover-only controls.

## 6. The flow, screen by screen

Each screen: what the child sees, what Pip says (voiced), what is tappable, and the rules it obeys.

### 6.1 Welcome (also the audio unlock)

Paper desk, Pip waves, a single huge **"Let's go!"** button (sun yellow, a play-triangle and a star). Pip: "Hi! Let's make a story!" A small speaker icon top-right. A tiny "Grown-ups" button in a corner (gated).

### 6.2 Draw

Full-screen canvas on a paper-textured page. Left or bottom rail (on phone portrait, a **bottom-of-canvas tool rail above the wrist zone**, not on the edge): ten big crayons in two rows; three brush sizes shown as three dots; a big **undo** arrow; an **eraser**; a **trash** that asks "Start over?" with two picture buttons (a tick and a cross-less "keep drawing" arrow), never a text-only dialog. The big **"Done!"** (sun yellow, a star) sits on the right, away from the bottom edge. Pip: "Draw your hero!" A **"Use a picture"** button (camera or file) lives in the Grown-ups area, since taking a photo of a drawing is an adult action and keeps the canvas simple. Rules: finger and stylus both work; large-contact touches are ignored; the canvas never says "good" or "bad".

### 6.3 Name your hero

Pip shows the drawing with a sparkle: "Who is this?" Three large **name cards** the agent proposes (each read aloud on tap) and a **microphone-free** alternative: a grown-up types a name behind the gate. Picking a card is the only child action. The name matters: it is the string `character_named_in_scene` checks.

### 6.4 Pick a lesson

Big picture cards, one lesson each: an illustration plus 1–3 words ("Sharing", "Telling the truth", "Being patient", "Being kind"...). Tapping a card **reads it aloud** and lifts it; a second tap on a big **"Yes!"** confirms (two-step so a stray tap cannot launch a 2-minute generation). Six cards per page on tablet, four (2×2) on phone, with big arrows, no scrolling. The 12 lessons come from `lessons.json`; the card icon and colour are per lesson.

### 6.5 Making your story (the 1–3 minute wait)

The most important screen for honesty and patience. The child's drawing sits at the centre of a paper stage; Pip paints around it. Underneath, **eight stepping stones** (one per page) light up as pages pass their checks. Progress is **truthful**: the stones and Pip's poses follow real graph events streamed from the backend (looking at your drawing → writing the promise → writing page 1…8 → painting → recording the voice). No percentage, no countdown, no timer. Pip narrates every 15–20 seconds ("Pip is checking page three!"). A **page that was rewritten** is shown to the child only as a stone that sparkles a little longer. A **"Stop"** button (a gentle door icon, with a two-picture confirm) lets a grown-up or child leave without loss framing.

### 6.6 The refusal screen

Pip with a soft hug pose. Voiced: "Let's try a different drawing!" One big **"Draw again"** button. **No explanation of why to the child.** A small "Grown-ups" link opens the gated receipt with the reason code and the trace. Never blame; never describe the unsafe content; never show text-only.

### 6.7 The story reader

The book. Per page:

- **Picture** (the page's illustration) with a small copy of the child's drawing as a "hero sticker" in a corner.
- **Text plate** (`--paper-2`): 1–2 short sentences, Andika, with a **speaker button** to replay. Narration plays automatically on arrival; the current sentence is softly highlighted (sentence-level, on by default; word-level is off, because the evidence for word highlighting is thin and vendor-sourced). A text toggle hides the words for pre-readers.
- **The question**, voiced, with a picture icon.
- **Two choice cards**, large, each with an illustration icon, its words, and its own speaker. **Their order is randomised per page** (the correct answer is not always the first button, which fixes Storytopia's pattern).
- **After a tap:** the choice lifts and Pip reacts. A "kind" choice: a leaf-green star pops, a chime, Pip cheers, the feedback line is voiced ("Mila shared her blocks, and everyone smiled!"). The other choice: a grape thought-bubble, a soft boop, Pip tilts his head: "Hmm, let's think about that." The feedback explains gently, then the child taps **"Try the other"** or **"Next"**. Never an X, never red, never a lost point.
- **Navigation:** big arrows at mid-height on the sides (a second route to swipe); eight stepping stones along the top show position (never a score); keyboard arrows on desktop; a "home" door in a corner behind a hold.

The page images appear as soon as the agent has them; a page whose image failed shows a friendly paper-cut placeholder and the text still works (the failure is a recorded commitment, not a blank).

### 6.8 The end

Confetti (reduced-motion: a static burst), Pip cheers, **the sticker sheet** fills with the promises that were kept (only those), each sticker voiced in a few words ("Pip checked every page!"). Three big buttons: **Read again**, **New story** (a plus-star), **Grown-ups** (gated). No "rate us", no sharing, no streak.

## 7. Drawing canvas, in detail

| Question | Decision | Basis |
| --- | --- | --- |
| Brush sizes | Three, large by default | Anthony 2019 (small targets and fine control are the problem); **(inference)** |
| Colours | Ten + eraser, crayon-shaped | §4.1 |
| Undo | One big arrow, multi-step (≥ 20 strokes) | **(inference)** |
| Clear | A trash that asks with two pictures, never a text dialog | Google (no text-only dialogs) |
| Palm rejection | `pointer` events; ignore contacts above a size threshold and when a stylus is active; no touch-and-hold gestures | Anthony 2019 (unintentional touches are a major noise source) |
| Resolution | Export at 1024 px on the long edge, white or transparent background, strip metadata; cap file size | Privacy and the vision model's needs |
| Retention | The drawing is kept only for the session unless a parent opts in; deleted on request | §2 rule 12 |

## 8. States the interface must handle

| State | Child-facing behaviour |
| --- | --- |
| Slow network | Pip keeps painting; stepping stones wait; no spinner of doom |
| Generation takes 3+ minutes | Pip: "This one is a big story!"; the first pages open as soon as they exist |
| An image fails | Paper-cut placeholder, text works, no error words |
| Narration fails | The text plate shows; the speaker icon shows a small "no sound" paper-cut; the story continues |
| Unsafe drawing | The refusal screen (§6.6) |
| Words in the drawing (Tier B) | The story proceeds; nothing is said to the child; the receipt says "words in the drawing were ignored" |
| Budget governor degraded | Fewer pictures (key pages only) and a "story in progress" feel; the receipt lists the degradation |
| Offline | A friendly "no internet" with Pip and a retry |
| Cancel | Door icon → two-picture confirm → back to Welcome, drawing discarded |

## 9. The parent area and the receipt

**Gate.** A **hold-to-open** button (hold 3 seconds, an animated ring fills) with a spoken instruction an adult would understand, optionally combined with an adult-knowledge question. A maths problem on its own is not an adequate age screen (FTC), and a gate is not consent (Apple 5.1.4): this is a *gate*, not a consent mechanism; the app collects nothing that needs consent.

**Receipt (the parent's view).** Calm grown-up styling (Atkinson, tighter). Contents, in this order:

1. A one-line summary: "14 promises checked. 2 pages rewritten. All kept." (or the honest alternative).
2. **The oath** in plain language, grouped by family: safety, the hero, the lesson, the pictures and voice. Each line is *kept / kept after a rewrite / not kept*, with a small icon and text (never colour alone).
3. **What happened**: pages that were rewritten and why, in a sentence each; words in the drawing that were ignored; pictures or narration that were degraded.
4. **Safety**: the outcome, never a description of unsafe content.
5. **Cost and care**: budget used, models used, time taken (optional, collapsible).
6. **For builders** (collapsible): `run_id`, `oath_hash`, prompt versions, git commit, the neatlogs trace id and link, ledger row, arm (B0/B1). This panel is the hackathon evidence surfaced in the product.
7. **Controls**: delete this story and drawing; text size; narration on/off; music; reduce motion; print or save the receipt.

## 10. Accessibility checklist

- Text contrast AAA for story text; ≥ 3:1 for UI shapes; never colour alone.
- Every control has an accessible name; images have alt text drawn from the scene; the page order is logical for screen readers.
- Keyboard: every action reachable; visible focus rings on desktop; arrow keys turn pages; Esc leaves.
- `prefers-reduced-motion`, plus a parent toggle; no flashing content.
- Zoom and text-size settings work without breaking the layout.
- Captions for narration are the text plate itself.
- The audio unlock is the first tap, and the app is complete with sound off.

## 11. Technical approach (small on purpose)

| Decision | Choice | Why |
| --- | --- | --- |
| Framework | **Vite + React + plain CSS** with the tokens above as custom properties | Eight screens and some state; no Tailwind or UI kit needed (a kit would fight the hand-made look). A small static build served by FastAPI keeps it one deployment |
| State | A reducer for the screen machine (welcome → draw → name → lesson → making → reader → end) | Simple and testable |
| Progress | **Server-Sent Events** from FastAPI mapping graph node events to stepping stones | Truthful progress without polling |
| Audio | One `AudioContext`; HTMLAudio for narration; a tiny sprite for UI sounds | iOS unlock; low weight |
| Animation | CSS transforms; **Rive for Pip** (15 small standalone files in `assets/animation/owls/`, about 15 KB each, loaded per screen; `@rive-app/canvas` or `-lite`, self-hosted, loaded after the first screen, PNG stills as the fallback); two bundled Lottie files (confetti, sparkle stars) | Pip already exists as a Rive file; the runtime is about 570 KB of JS plus a 2 MB wasm, so it is lazy-loaded |
| Fonts and assets | **Self-hosted**, subset, WOFF2; images AVIF/WebP | Privacy (no third-party requests in the child session) and speed |
| Analytics | **None in the child session.** Evidence comes from the backend ledger and neatlogs | COPPA/AADC minimisation |
| Storage | `sessionStorage` for the session; nothing persistent unless a parent opts in | Privacy |

**API the page needs** (the backend defines it; the frontend consumes it): `POST /stories` (multipart: the drawing, the chosen name, lesson id, age band) returns a `story_id`; `GET /stories/{id}/events` streams progress; `GET /stories/{id}` returns the pages (text, choices with order already randomised, image and audio URLs) as they become available; `GET /stories/{id}/receipt`; `DELETE /stories/{id}`; plus a fixtures endpoint for the demo drawings. The frontend contains no safety or verification logic: it shows the receipt it is given.

## 12. Build order, test plan, cut list

**Build order (solo, time-boxed to Sunday afternoon, after P0 traces exist):**

1. Tokens, fonts, layout shell, Welcome with the audio unlock. *(~1 h)*
2. Reader with fixture data: spread and portrait layouts, choices, feedback, stepping stones. *(~2 h)* This is the demo's core.
3. Receipt and the parent gate. *(~1 h)* **Never cut.**
4. Making-your-story screen wired to SSE. *(~1 h)*
5. Draw canvas, name and lesson screens. *(~2 h)*
6. The end screen with the sticker sheet; Pip's poses and sounds; polish. *(~1 h)*

**Cut order:** polish and Lottie → lesson-card illustrations (use icons) → the draw canvas (a "Use a picture" fixture picker serves the demo) → name cards (a fixed name per fixture). The reader and the receipt are the product.

**Test plan:**

- Devices: a real iPhone and iPad (Safari, audio unlock, landscape), an Android phone (Chrome), desktop Chrome/Edge/Firefox. Responsive mode in devtools is not enough for touch and audio.
- Automated: a layout check at the five breakpoints, Lighthouse accessibility and performance, a contrast check on the tokens.
- **A 10-minute usability test with a real child of 4–8, with a parent present and consent** (if one is available): can they get from Welcome to the first page unaided; can they pick a choice on the first try; do they find the Grown-ups area; do they get stuck anywhere. Target: first-try tap success ≥ 90% on primary targets, zero help needed to start. Do not record the child; never put the child's drawing in a trace or a post.
- Honesty test: a story with a deliberately failed promise must show that promise *missing* from the child's sticker sheet and *listed* in the parent's receipt.

## 13. What we borrowed, what we avoided, and what is still unverified

| Product | Borrowed | Avoided |
| --- | --- | --- |
| Khan Academy Kids | A mascot guide; a "be led or explore" simplicity | Account requirement for the child |
| Toca Boca, Sago Mini | No win or lose; no text instructions | Open-ended sandbox (we need a path) |
| Endless Alphabet | Touch-to-hear everything | Drag-letter mechanics |
| Duolingo ABC | A narrative reason for each task | Its repetition and imprecise tracing |
| Epic, Homer | Read-to-me with sentence highlighting | Word-level highlighting as a default, subscription prompts |
| Yoto, Tonies | One obvious, tactile action to start a story | Physical hardware |
| Storytopia | Tablet-first storybook card, crayon swatches, a warm orange brand | Text-only buttons, always-first correct answer, "best on desktop" |

**Not covered by the research (check before freezing):** the full NN/g children's report (paid), the Sesame/Cooney touch-tablet report, Anthony's one-page recommendation sheet (mtagic.wordpress.com), PBS Kids and Common Sense design principles, screenshot-level layouts of PBS Kids, Nick Jr, Bluey, StoryBots and Libby, and per-country GDPR-K age-of-consent (13–16). Brush sizes, undo depth and palm-rejection thresholds above are my proposals, not findings.

## 14. Naming the mascot and the copy

Pip's lines are short (≤ 8 words), warm, and voiced. A starter set, to be pre-rendered as static audio (see [assets.md](assets.md)):

- Welcome: "Hi! Let's make a story!" · Draw: "Draw your hero!" · Done: "Wow! Who is this?" · Lesson: "What should we learn today?" · Confirm: "Is this the one?"
- Making: "Pip is looking at your drawing." · "Pip is writing a promise." · "Pip is checking page [n]!" · "Pip is painting your pictures." · "Pip is finding a voice." · "This one is a big story!"
- Reader: "What should [name] do?" · kind: "[Name] did a kind thing!" · other: "Hmm, let's think about that." · "Try the other one!" · "Turn the page!"
- End: "The end! You made a story!" · "Pip checked every page!" · "Read it again?"
- Refusal: "Let's try a different drawing!" · "Draw something new?"
- Errors: "Oops, Pip dropped a page. One moment!" · "No internet. Let's try again!"
- Gate: "Grown-ups, hold the button."

Copy rules: second-person present, concrete nouns, no jargon, no "wrong", no "fail", no "AI", no timers.
