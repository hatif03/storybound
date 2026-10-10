# Storybound brand: quick guide

## Colours
| Name | Hex | Use |
| --- | --- | --- |
| Cream | `#FFF8EA` | backgrounds (about 60%) |
| Ink | `#2A2745` | text and outlines (about 30%) |
| Sun | `#FFC93C` | the brand colour: badge, buttons, avatar background |
| Tangerine | `#FF9A3C` (text: `#E8710A`) | the word "bound", highlights. Use the darker `#E8710A` for text on cream |
| Berry `#FF7096`, Sky `#59B8F3`, Leaf `#6CC57A`, Grape `#8F73E0` | small accents, the promise stickers |

## Type
Wordmark: Fredoka Bold, converted to outlines (no font needed). Headlines in images: Fredoka 700. Body and captions: Atkinson Hyperlegible.

## The logo
A scalloped seal badge (an oath seal, with ribbon tails for "bound") holding Pip's face; wordmark "Story" in ink and "bound" in orange.
- `logo/storybound-mark.svg` the badge alone (use for avatars, app icon art)
- `logo/storybound-lockup-horizontal.svg` badge + wordmark side by side (default)
- `logo/storybound-lockup-stacked.svg` badge above wordmark (title cards, square spaces)
- `*-on-dark.svg` white "Story" + orange "bound", for ink or dark backgrounds
- `logo/storybound-wordmark-{color,ink,white,on-dark}.svg` wordmark only
- PNGs are exported next to the SVGs (transparent).
Keep clear space of at least a quarter of the logo height. Do not stretch, recolour, add shadows to the wordmark, or put the horizontal lockup below about 120 px wide (use the mark instead).

## Favicon
A simplified, flat vector Pip (so it stays readable at 16 px) on a sun-yellow rounded square: `favicon/favicon.svg`, `favicon.ico` (16, 32, 48), PNGs at 16/32/48/180/192/512, `apple-touch-icon.png`, `maskable-512.png`, `site.webmanifest` and `head-snippet.html` (paste into the page head).

## Social and video images
`social/`: `og-1200x630`, `github-social-1280x640`, `x-post-idea`, `x-post-trace` (an illustration, not real data), `x-post-numbers-TEMPLATE` (placeholders "?? of ??": **fill from the ledger before posting, never post as is**), `x-header-1500x500`, `x-avatar-400x400`, `readme-banner-1600x400`.
`video/`: `title-card`, `end-card` (sponsor logos on equal white chips, following Entire's clear-space rule), `thumbnail-1280x720`, three transparent `lower-third-*` overlays, and five transparent `five-points-*` overlays (architecture, implementation, runtime, reasoning, result) for the per-tool segments.

## Regenerating
`_source/make_brand.py` rebuilds everything from the assets folder (it needs Python with Pillow, fontTools, uharfbuzz and Microsoft Edge; `wordmark.py` produces `wordmark.json`). The sponsor files are not altered; Entire's rules are in `sponsors/README.md`.
