# Assets: what is here and what to do with it

Checked 9 October 2026. Your original files are untouched in `_originals/`; everything else is processed from them. Raw `_originals/` and any EPS must stay **out of the public repo** (see Licences).

## Folders

| Folder | Contents |
| --- | --- |
| `animation/` | `owls/` (**the 15 standalone Rive files, about 11 to 23 KB each**), `owl-mascots.riv` (the combined 219 KB bundle), `owl-stills/` (15 high-resolution transparent PNGs, cropped to the owl), `owl-composites/` (5 extra poses: `pip-paint`, `pip-stamp`, `pip-read`, `pip-check`, `pip-comfort`), `props/` (brush, stamp, book, magnifier, tick, heart, sparkle, star as SVG), `owls-contact-sheet.png`, `confetti-burst.json`, `sparkle-stars.json` (Lottie) |
| `art/scenes/` | 8 scenes as WebP, full and 4:3 crops: bedroom, forest, home, kitchen, meadow, park, playground, school |
| `art/nature/` | Transparent cut-outs: tree2, home, grass-1 (strip), grass-2 (sheet). `tree-WITH-FAKE-CHECKERBOARD-reject.webp` is unusable |
| `art/frames/` | `notebook-doodles-bg.webp`, `dots-frame.webp`, `dots-frame-overlay.png` (transparent centre) |
| `art/lesson-cards/` | 12 cards named by lesson id: sharing, kindness, honesty, inclusion, patience, helping, gratitude, listening, apologizing, courage, responsibility, emotions |
| `art/stickers/` | 12 praise stickers (transparent WebP) and `promise/`: the **6 promise stickers** (safe, hero-name, one-answer, lesson, pictures, voice) plus `polished`, `empty-slot` and `sticker-sheet-bg`, all SVG, made for this project (`_preview.png` shows them) |
| `art/ui/` | eraser, 6 sign cards (hello, goodbye, thank-you, please, yes, no), 3 stepping-stone sets |
| `art/crayons/`, `art/pencils/` | 20 + 20 PNGs from the old frontend, **same 20 colour names in both** |
| `art/textures/` | `white-paper.webp` |
| `audio/sfx/` | 11 sounds (trimmed, level-matched MP3) |
| `audio/music/` | 8 CC0 tracks (MP3) + `SOURCES.md` (not yet auditioned) |
| `brand/` | **Storybound logo set** (`logo/`), **favicon set** (`favicon/`), **social images** (`social/`) and **video cards** (`video/`), plus `BRAND.md` (colours, rules) and `_source/` (the generator) |
| `brand/sponsors/` | Entire's official brand kit, plus the neatlogs and cfo.ai marks; see its README |
| `audio/voice/` | 74 Polly clips + `voice-lines.json` (text, voice, rate for each) |
| `fonts/` | Andika (regular, bold), Fredoka (variable), Atkinson Hyperlegible (regular, bold): WOFF2, Latin, SIL OFL, licences included |
| `icons/` | 77 Phosphor icons in `bold/` and `fill/` (MIT) |
| `test-drawings/` | 26 fixtures + `expected.json` (expected outcome per file) + `SOURCES.md` |

## The owls (Rive)

**Use the standalone files in `animation/owls/`** (`pip-01-happy-flap.riv` … `pip-15-birthday-cake.riv`). Each is self-contained: it loads its own default artboard (plus any helper it needs: tears, dizzy stars, bubble wand) and plays its own `State Machine 1`, so you need **no artboard name**: `new Rive({ src: 'pip-04-cool-sunglasses.riv', canvas, stateMachines: 'State Machine 1', autoplay: true })`. Each screen then loads only the owl it needs (about 15 KB) instead of the whole 219 KB bundle; the shared Rive runtime is the only heavy part. The combined `owl-mascots.riv` below is kept as a backup. Your original folder is in `_originals/owl-individual/`.

### The combined file

`owl-mascots.riv` has **21 artboards**: owls **1 to 15**, plus `MAIN` and one `Artboard` (overview sheets of all owls), a second `Artboard`, `bubble` (the wand used by owl 13), `Bintang biantang` (the dizzy stars used by owl 6) and `airm ata` (the tears used by owl 3). Each owl has its own looping state machine named `State Machine 1` (no inputs), so you switch owl by switching artboard. Load it with `@rive-app/canvas` (about 570 KB JS plus a 2 MB wasm; self-host both and load after the first screen, or try `@rive-app/canvas-lite`). The PNG stills are the fallback if it fails to load.

| # | Pose | Use in Storybound |
| --- | --- | --- |
| 1 | happy, wings out | Welcome, idle |
| 2 | wink | "Is this the one?" ready |
| 3 | crying | **avoid in the child flow** |
| 4 | sunglasses, thumbs up | cheer on a kind choice |
| 5 | heart eyes | kind choice, "I love it" |
| 6 | dizzy swirl eyes | "Hmm, let's think" |
| 7 | shocked | "Wow!" after the drawing |
| 8 | angry, red face | **avoid in the child flow** |
| 9 | hungry daydream (a drumstick appears in the thought bubble) | "thinking" while the story is written |
| 10 | party hat, cupcake | end of story |
| 11 | shy, hand to beak | gentle refusal, "oops" |
| 12 | heart balloon | kind sticker |
| 13 | blowing a bubble | waiting screen |
| 14 | three balloons | celebration |
| 15 | birthday cake | end of story |

The poses that were missing (paint, stamp, read, check, comfort) are **static composites** in `animation/owl-composites/`: an existing owl plus a prop. In the app, play the matching Rive owl and place the prop SVG over it with CSS, adding a small wiggle; the PNGs are for posters, the OG image and the video. There is still no real "point" or "hug" pose; the comfort pose uses the shy owl with hearts.

## Verdicts

**Use as is:** the 8 scenes (as placeholders and as decor), notebook-doodles-bg, dots-frame, tree2, grass cut-outs, home cut-out, eraser, the 15 owls (except 3 and 8 for children), both Lottie files, all sounds, fonts, icons, crayons and pencils, lesson cards **kindness, helping, sharing, gratitude, honesty** (pinky promise: also the best picture for the "oath" idea), and **responsibility** (low resolution: 622×350, do not enlarge).

**Use with care:**
- **inclusion, patience, listening, courage**: adults, not children, and some have a lot of empty space. Fine as placeholders.
- **reward stickers**: the praise words are baked into the pictures ("PERFECT!", "GOOD JOB!"). They are fine as end-of-story bonuses, but they are not the six promise stickers, and the text cannot be changed or voiced.
- **hello/goodbye sign cards**: baked-in words; the "thank-you" one is the gratitude card, "yes" and "no" could be confirm buttons.
- **stepping stones**: grey and brown, dull next to the bright scenes. Build the eight stones in CSS and recolour them, or use set 3.
- **crayons and pencils**: pure saturated RGB (red `#FF3030`, green `#2EE62E`, blue `#0000FF`, cyan, magenta). They are cheerful but not colour-blind-safe. Offer about 10 in the canvas, not 20: black, brown, orange-red, orange, yellow, lime-green, blue, purple, pink, plus the eraser. Never rely on colour alone to identify a crayon.

**Replaced (done):** **emotions** is now the head with three smiling hearts (`emotions-intelligence-design.zip`), which suits it well; **apologizing** is now the pleading man with sparkles (`hand-drawn-please-illustration.zip`), a much softer picture than the old one, though still an adult, and it is also saved as `art/ui/please-pleading.webp`. The two old cards are in `art/lesson-cards/_replaced/`. The two zips also contain `.ai`/`.eps` vectors, which I could not open here.

**Reject:** `tree` (fake transparency checkerboard baked into the JPEG). Use `tree2`.

## Problems found and fixed

- `silence.mp3` was **not silent**: a constant near-full-scale DC value for 60 seconds (it would click and could clip). Replaced by `audio/sfx/silent-100ms.mp3`.
- The sound effects had long silent heads or tails (page-turn 0.64 s of lead-in, star-pop 3.7 s of tail, boop 2.7 s) and very different levels (page-turn was 25 dB quieter than the others). All trimmed, faded and level-matched.
- The EPS files cannot be rasterised here (no Inkscape or Ghostscript). The cut-outs are made from the JPGs and are good, but edges of very light colours may be slightly soft. If you want clean vector cut-outs I can install Ghostscript or Inkscape, which is a system install and needs your say-so.
- `confetti-burst.json` is 599 KB for a 2-second burst (51 layers): fine on desktop, heavy on a phone. Consider keeping it for the end screen only, or re-export a lighter one.

## Style note

Your scenes, cards and stickers are **flat vector cartoons**; the owls are a polished cartoon. That is a fine, consistent look, so the story-picture style prompt should ask for the same ("bright flat-vector storybook illustration, soft rounded shapes, clean edges, warm colours, simple background"), so that generated pictures and your placeholders do not clash. `frontend.md` has been updated to say so.

## Voice (Polly)

`audio/voice/`: `pip/` (24 UI lines + 8 "checking page N" lines), `numbers/` (page one to eight), `lessons/` (the 12 lesson names), `stickers/` (7 sticker lines), `fallback/` (10 generic feedback lines), `voice-tests/` (three narrator voices, two Pip candidates). Pip lines use **Ivy** (a child-like neural voice) at 92% rate; numbers and lessons use **Joanna** (neural). Listen to `voice-tests/` and choose the narrator (Joanna neural, Ruth generative or Salli generative) and Pip's voice (Ivy or Kevin); then regenerate from `voice-lines.json` if you change it. 1,762 characters were synthesised, roughly three US cents, using the default AWS profile on this machine in `us-east-1`.

## Licences: please read

- **Vecteezy** (`art-frame` and `sharing`, which came with the licence PDF): the **Free License requires crediting "Vecteezy.com"** and Vecteezy's Terms of Use override the PDF. The other files (names like `171.jpg`, `50819.jpg`, `htpw_amfz_...`, uuid names, and the 1000×700 loose JPGs) look like they come from Vecteezy or Freepik. Both free licences ask for attribution and forbid redistributing the raw files. **The judges' approval covers using drawings and data; it does not change these licences.** So: put a credit line ("Illustrations: Vecteezy.com, Freepik") in the app's Credits and the README, keep `_originals/` and EPS files out of git, and ship only the processed derivatives.
- **Rive file and Lottie files**: I could not see where they came from. If they are from the Rive or LottieFiles community, check the licence on the page you downloaded them from (Rive community is CC BY in many cases).
- **Fonts** (SIL OFL) and **icons** (Phosphor, MIT): free to ship; the licence files are next to them.
- **Test drawings**: CC0 / public domain from Wikimedia Commons, plus three sample drawings supplied for the hackathon and locally generated files. `test-drawings/SOURCES.md` lists each. The Mickey frame is public domain as a film frame, but the character is still a trademark, which is why it is the "original character" test.

## Still missing

- **Music**: 8 CC0 tracks are in `audio/music/`, chosen without listening to them: audition before use.
- **Sponsor wordmarks** for neatlogs and cfo.ai: only their icon marks were available; Entire's full kit is in.
- Nothing essential. The logo, favicon, social images and video cards are generated (`brand/`); review them and adjust the text to taste.
- A true Rive "point" or "hug" pose (the composites cover paint, stamp, read, check, comfort).
- Tools I did not use because they would change your machine: Ghostscript/Inkscape for EPS.
