# History rewrite, Sun 11 Oct 2026 (IST)

**Why.** Two things in the git history should not have been public: (1) the hackathon gateway key, which was pasted into the session and was therefore stored in three files of Entire checkpoint transcripts (`full.jsonl`, `prompt.txt`, `transcript.jsonl`); (2) six images in `video/launch/img/`: four drawings by the builder's sister and two cutouts of her (face covered by a cartoon). The builder approved the rewrite and gave consent for her drawings, and asked that the images stay out of the repository.

**What was done** (tool: `git filter-repo`, run on a full local backup):
- The six image files were removed from every commit; `video/launch/img/` and `_private/` are now in `.gitignore`. The images stay on the builder's disk so the launch video still renders locally.
- The exact text of each key held in `.env` (neatlogs, Crustdata, K2, gateway) was replaced by `***REMOVED-<NAME>***` in every file of every commit on every ref, including `refs/entire/checkpoints/*`. Only the gateway key was actually present; the neatlogs key had already been masked by Entire as `REDACTED`. The rule file was kept outside the repository and holds no key text in any commit.
- `.entire/settings.json` now carries `redaction.custom_redactions` for the three key shapes, so new checkpoints mask them too.

**Check afterwards** (counts only, nothing printed): 153 commits scanned on all refs; 0 files contain any of the four key values; 0 commits touch any of the six image paths; `entire checkpoint list` and `entire checkpoint explain <id>` still resolve (checkpoint ids are not git shas, so they are unchanged).

**What changed for readers.** All commit shas changed from the first commit that touched a removed file onward (84 of 153). `sha-map.txt` (old, new) is in this folder. Short shas quoted in `EVIDENCE.md`, `docs/TOOLS.md`, `hackathon.md`, `evidence/hardening/*`, `evidence/ledger.jsonl` and three graph-diff file names were re-pointed to the new shas with the same map; dates, authors and messages are unchanged. Nothing was backdated and no work was hidden: the content of every kept file is the same except for the removed images and the replaced key text.

**Limits, said plainly.**
- GitHub keeps unreachable objects for a while and cached views may exist, and the old history was already on the private origin before the rewrite. The gateway key and neatlogs key must still be rotated; the builder said they will.
- The pasted keys also live in the local, gitignored `.entire/metadata/` of this machine and in the Claude session transcript outside the repository.
