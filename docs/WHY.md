# Why a parent would want Storybound, and who it helps

Written for: parents, teachers, librarians and anyone who is not an engineer. No jargon; every number points to a file in this repository.

## The problem in one minute
Computers can now write a bedtime story about your child's own drawing in seconds. That is wonderful and a little frightening. A story model is a fast, fluent writer that has no idea what is right for a five-year-old, and nobody is watching it. In our own experiment, the same story writer, left alone, slipped at least one broken promise into **27 of 28** stories: a lesson that never appeared, a question where the right answer was always the first one, sentences too hard for the age, and sometimes an unkind line. Reading every story first is exactly what a busy parent cannot do, and if a child is on a tablet the parent is not there to check.

So today a parent has two choices: do not use these tools, or trust them blindly. Storybound is a third choice: **use them, and check them**.

## What Storybound does, in four steps
1. **A child draws a hero** (or a grown-up photographs a drawing) and picks a lesson: sharing, honesty, kindness or patience.
2. **A helper writes down its promises first.** Before there is any story, the agent writes a short oath for this drawing and this lesson: it will keep to age-appropriate words, show the hero on every page, actually teach the lesson, avoid scary or unkind things, and not paint stray words into pictures. A grown-up can add a promise of their own ("nobody in the story is left out").
3. **It checks every page before the child sees it.** A page that breaks a promise is rewritten, and only then shown. Each page comes with a picture and a warm voice reading it aloud, then a gentle choice ("What should Sam do with the blocks?") where a wrong answer is never a scolding. After the story there is a short quiz and a picture game, and the app can make a read-along movie of the story.
4. **The grown-up gets a receipt.** A plain page behind a grown-up gate says how many promises were checked, which pages had to be rewritten, and anything that could not be fully kept. Nothing is hidden. The result: **0 of 28** stories shipped with a broken promise when every page was checked, against 27 of 28 without.

Think of it as the nutrition label for a bedtime story.

## Why a family would try it
- **It makes a story out of what the child made.** Their own drawing becomes the hero. That is a reason to pick up a pencil, not only a screen.
- **You do not have to read it first.** The checking happens before the child sees a page, and the receipt tells you afterwards what it did.
- **It reads to the child.** A page opens, the picture is already there, and after a short pause the story reads itself aloud. A child who cannot read yet, or who is learning English, can listen on their own and replay any page.
- **It is gentle by design.** No accounts, no ads, no purchases. No timers, streaks, scores or "come back tomorrow". After two stories Pip suggests resting the eyes. Everything that throws work away needs a hold, not a tap. A parent can make the app forget a story, which deletes it.
- **It gives parents something to talk about.** Each story ends with a question for a grown-up to ask ("What do you like to share with your friends?").

## Community impact: why it matters beyond one family
- **A pattern other children's tools can copy.** The idea that matters is not a story app. It is that anything an AI makes for children should come with promises written down in advance, checked before delivery, and a receipt a parent can read. This repository is open so anyone building for children can reuse it.
- **Trust that can be checked.** Every claim here is backed by a recorded run in `evidence/`. We also say what did not work (a cheaper writer failed three stories in ten; a mistake of our own made the check screen look like a refusal) and how we fixed it.
- **Cheap enough to give away.** A story costs about two cents of text and roughly twenty cents with pictures and a voice (text measured with neatlogs, pictures and voice estimated; modelled with cfo.ai). That puts it within reach of schools, libraries and community groups, not only paying households. Video clips, which would cost far more, are left out on purpose ([BUSINESS.md](BUSINESS.md)).
- **Reading aloud for children who are read to less.** Parents who work long hours, are learning the language, or find reading hard can still give a child a story that reads aloud, in a calm voice, with a lesson that matches what the family cares about. We do not claim it replaces a parent; a gentle conversation card nudges the grown-up to join in.
- **Privacy by default.** The drawing stays on the server only until a parent taps Forget (the public demo also wipes everything after 24 hours), nothing is sold, and no real child's data is used in our traces, tests or posts.

## What it is not (honesty matters for children's tools)
- It is a prototype built in three days, tested with fixture drawings and one family tester, not a product tested with many children. Ten to thirty stories per experiment is a small sample.
- The checker is another AI model, not a person; the human review of its verdicts is only just under way ([TOOLS.md](TOOLS.md)).
- Stories are in English; a Hindi or Spanish caption on a drawing is ignored, never repeated, but we have not built translation.
- A story can still be imperfect; that is why the receipt exists. In our own demo recording the receipt reads "26 promises checked, 4 could not be fully kept", and it says so.

## See it
- The three-minute video, the full tour with the grown-up side, and the live app: see the top of the [README](../README.md).
- The numbers behind this page: [STORY.md](STORY.md), [HR-014](../evidence/hardening/HR-014.md), [HR-015](../evidence/hardening/HR-015.md), [BUSINESS.md](BUSINESS.md).
