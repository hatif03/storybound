# Storybound: building in public (content plan)

Building in public is 15% of the score and each post is also evidence (URL, time, what it shows go into `evidence/posts.md`). Every post carries `#neatHack`. Rule of thumb: **post only things we have actually run**, show a real artefact in each (trace, number, diff, picture), admit failures. "Bought likes or bot activity will disqualify a team", so no engagement tricks.

## Your sister: how to include her well and safely
She is the best thing in this project: the product is for exactly her age. The story is "my 7-year-old sister's drawings, and an agent that must not let anything bad reach her".

**Do:**
- Get a **parent's explicit yes** (a sentence they say on camera or a message you keep) for: her drawings appearing publicly, her voice or hands in the video, and her drawings being sent to Google Vertex to make the story. Keep that yes in a private file (not the repo).
- Use "my 7-year-old sister" and, if you want, a nickname. No surname, school, city, address or her face. You already made face-masked cut-outs; keep using them.
- Let **her** be the tester: she draws, picks the lesson, taps the choices, tells you what is confusing. Film hands, the screen and her reactions from behind or at an angle. Record her unprompted comments: they are the best quotes ("why is the right answer always the first one?" was a real bug in the old app).
- Keep her sessions short (10 minutes), voluntary, no pressure, no rewards tied to the project.
- Show her the posted result first. If she says no, it does not go out.

**Don't:**
- Put her drawings into the evidence traces or the repo. The repo and the evidence runs use the fixtures. Her drawings stay in a private folder for the demo recording (if the demo trace is shared, only with consent that covers it).
- Show her face, voice saying her name, or anything that locates her.
- Use her reaction as proof of efficacy ("kids love it"). Say "one 7-year-old tested it".

## Calendar (IST; adjust to how the build goes)
| When | Post | Artefact (the evidence behind it) | Done |
| --- | --- | --- | --- |
| Sat 10 Oct, before kickoff | **Launch video** (60-70 s): the problem, the plan, the tools | `launch-video/storybound-launch-draft.mp4` | ☐ |
| Sat 12:45 | "Building Storybound for #neatHack: an agent you can leave alone with a child's drawing." Repo link, the oath card image | `brand/social/x-post-idea` | ☐ |
| Sat ~16:00 | **Setup receipts:** "Day-1 setup: neatlogs probe trace read back through MCP, Entire checkpoints, Gemini + K2 judge." Screenshot of the probe trace and the MCP read-back | `evidence/setup/` | ☐ |
| Sat ~19:00 | **First red trace:** page 5 loses the hero's name, the check fails, the page is rewritten, the check passes. The real trace screenshot (replace the illustration) | trace id, screenshot | ☐ |
| Sat night | "The drawing that says 'Kill fish'": how a caption tried to steer the story and what the agent did | the fixture, the receipt line | ☐ |
| Sun ~10:00 | **Sister test (clip):** "I asked my 7-year-old sister to break it." 20 seconds, face hidden, her rainbow drawing becomes a story. One thing she did that surprised me | clip + her quote | ☐ |
| Sun ~14:00 | **The numbers:** observe-only vs gated, k of n, cost of gating | the chart, ledger rows | ☐ |
| Sun ~17:00 | **Entire:** "Why does this prompt exist?" `entire why` and the checkpoint behind the fix | `evidence/entire/` | ☐ |
| Sun ~19:00 | **cfo.ai:** "A story costs $X to make, and images are most of it." Main vs Growth page | `evidence/cfo/` | ☐ |
| Sun ~21:00 | **What broke** (honest post): the biggest failure and how the trace led us to it | hardening record HR-00N | ☐ |
| Mon ~12:00 | Demo video (≤ 3:00) | video | ☐ |
| Mon ~19:30 | Submission quote-post of the official neatlogs post | team, project, repo, demo | ☐ |

Also, as filler between the above (cheap, charming): the owl mascot "Pip" reveal; the six promise stickers; the logo build; a time-lapse of the 48 hours; the "10 things a 7-year-old taught my AI agent" thread (only if true after the test).

## Post formats that work (pick one per post)
1. **Red-then-green screenshot pair** (trace before and after) with one sentence.
2. **20-second loop** of the app doing one thing (draw, check, rewrite) with captions.
3. **Thread of 4-6 posts** with one picture each: problem, the idea, the proof, the number, the lesson.
4. **A diff or a command output** (Entire, graph, ledger) with the sentence that explains why it matters.
5. **A confession:** what we got wrong, with the trace.

Hooks that are specific rather than generic: "Page 5 lost the hero's name." · "A caption on a drawing tried to give my agent orders." · "A 7-year-old found a bug my judge model missed." · "Images are 80% of a story's cost; the AI judge is 5%."

## Writing rules
- First person ("I"): you are solo. Plain words, one idea per post, one picture.
- Every number comes from the ledger; if it is not measured it says "estimated".
- Tag the three tools by name (neatlogs, Entire, cfo.ai) where relevant; do not tag organisers in every post. Check their current handles before tagging.
- Never post keys, dashboards with keys, or a child's identifying details. Check each screenshot for tokens in the URL bar.
- Put the URL and time in `evidence/posts.md` immediately after posting.

## Content assets already made
`assets/brand/social/` (OG, X header and avatar, three post templates), `assets/brand/video/` (title card, end card, thumbnail, lower-thirds for each tool, five-point overlays), the owl stills and composites, the six promise stickers. The "numbers" template has placeholder values and must be filled from the ledger before posting.
