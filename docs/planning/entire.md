# How Storybound uses Entire (v2)

Entire is how we **build** the agent, not a library the story calls. The story process never imports it. Companion to [plan.md](plan.md); see also [neatlog.md](neatlog.md) and [cfo.md](cfo.md). Written 9 October 2026 against [docs.entire.io](https://docs.entire.io/llms.txt) (CLI docs at 0.10.5) and corrected from [entire.v1.md](entire.v1.md). No application code.

neatlogs records what the **story agent** did. Entire records what the **coding agent** did when we wrote and fixed it. A neatlogs trace without a checkpoint, or a checkpoint without a trace, is half a submission. The pairing is the point: a `(commit sha, Entire checkpoint id, neatlogs trace id)` triple for every key change.

## 1. What the hackathon needs

[neatlogs.com/hackathon](https://neatlogs.com/hackathon): "Checkpoints or entire-graph output from your repository." Entire must have "a clear role in building the agent", and the three-minute video must cover it on five points: **architecture, implementation, runtime, reasoning, result** ([plan.md §12](plan.md#12-the-three-minute-demo)). Entire staff are judges. No Entire credits are listed. All code is written 10–12 October, so `entire enable` runs in the new repo after Saturday 12:30 IST, not in the folder holding the two source checkouts, and not today.

## 2. Corrections to v1 (verified against the docs)

| v1 claim | Fact | Source |
| --- | --- | --- |
| `entire enable -y --agent cursor`, `.cursor/hooks.json` | The team uses **Claude Code**: `entire enable -y --agent claude-code`. Hooks go into **`.claude/settings.json`** (existing settings preserved). Commit it. `entire agent add claude-code` is the hooks-only alternative | [quickstart](https://docs.entire.io/quickstart.md), [claude-code](https://docs.entire.io/agents/claude-code.md) |
| "Cursor transcripts have no token usage, so do not cite Entire for tokens" | True for Cursor only. **Claude Code token usage is captured**: `entire checkpoint tokens <id> [--compare <baseline>] [--json]`, `entire session tokens`. (`entire tokens` has only `tokens profile`, experimental) | [claude-code](https://docs.entire.io/agents/claude-code.md), CLI reference |
| `commit_linking` key is ambiguous, record it in `hackathon.md` | The key exists, default `"prompt"`, valid in `.entire/settings.json` or `settings.local.json` (not global). Set `{"commit_linking":"always"}` by **merging** into `.entire/settings.json`. No `entire configure` step needed | [settings-layers](https://docs.entire.io/guides/configuration/settings-layers.md) |
| "`entire status` saying hooks are active" | Plain `entire status` reports enabled or disabled. Use `entire status --detailed` and `entire agent list` | [status](https://docs.entire.io/cli-reference/status.md) |
| "`entire doctor` proves hooks are alive" | Doctor checks config drift, stuck sessions, logs and metadata-branch divergence. **The real test is: commit, then `entire checkpoint list`** | [agents/setup](https://docs.entire.io/agents/setup.md) |
| Redaction "covered" | Secret scanning is always on (Betterleaks, default true). PII redaction is **off by default** (`redaction.pii.enabled`). **Not redacted:** images, base64 images, `path` fields, shadow-branch snapshots, raw Claude session files. "Treat redaction as a safety net rather than a guarantee." Checkpoints live in the repo: "If your repository is public, so are they." The ULID in the trailer reveals creation time | [privacy-and-redaction](https://docs.entire.io/guides/configuration/privacy-and-redaction.md), [security](https://docs.entire.io/security.md) |
| Whether `git push` sends the checkpoint ref is unknown | **Yes by default** (`push_sessions: true`, a pre-push hook pushes queued per-checkpoint refs `refs/entire/checkpoints/<last-2-chars>/<26-char-ULID>`). A failed checkpoint push only **warns** and does not block the code push | [checkpoint-storage](https://docs.entire.io/guides/checkpoints/checkpoint-storage.md) |
| `entire why` / `blame` as durable evidence | They are **labs** commands, commit-level not line-level; rebase or squash reattributes. Good for the demo, not the durable record | [faq](https://docs.entire.io/faq.md) |
| Attach flow: "link it afterwards" | `entire session attach SESSION_ID --agent claude-code [--force]`; it may **amend the last commit and change its SHA**. Do it before pushing and re-record the SHA | [attach-sessions](https://docs.entire.io/guides/sessions/attach-sessions.md) |
| Subagents | File-changing subagents fold into the parent's next checkpoint. Read-only subagents are kept only when launched with `run_in_background` | [claude-code](https://docs.entire.io/agents/claude-code.md) |
| Git floor | Install needs Git 2.25+. **`entire graph` needs Git 2.36+ and CLI 0.10.0+** | [graph](https://docs.entire.io/cli-reference/graph.md) |
| Listed graph commands | Also `graph verify`, `graph commit`, `graph index`, `graph capabilities --json`, and Brain | [graph](https://docs.entire.io/cli-reference/graph.md) |

Still **unverified** and tested in spike S5: whether the VS Code extension runs the `.claude/settings.json` hooks; whether a plain `git clone` brings `refs/entire/*` down (by standard git it does not); whether entire.io shows a public repo's checkpoints to an anonymous viewer; whether `commit_linking` has a `"never"` value.

## 3. Install and enable (Windows, PowerShell, Claude Code)

Today: install the CLI only. Do **not** enable it anywhere.

```powershell
irm https://entire.io/install.ps1 | iex            # restart the terminal afterwards (PATH change)
entire version; git --version                       # Git >= 2.36 for entire-graph
Get-Command entire; Get-Command git-remote-entire
```

Git Bash refuses `install.sh` and points to PowerShell; use PowerShell to install. `entire` itself runs anywhere on PATH. If VS Code was open during install, restart it.

Saturday, after the first commit and after the GitHub remote exists:

```powershell
entire login                                        # browser; --device if no browser; Google sign-in exists
entire enable -y --agent claude-code
# merge {"commit_linking":"always"} into .entire/settings.json (do not overwrite)
entire status --detailed; entire agent list
entire plugin install graph
entire graph version
entire graph init-agents --repo .
entire graph doctor --json; entire graph capabilities --json
git add .entire .claude AGENTS.md CLAUDE.md .gitattributes
git commit -m "Enable Entire and entire-graph"
git push
git ls-remote origin 'refs/entire/checkpoints/*'
```

Then **start a new `claude` session**: an already-running session does not load newly installed hooks. Prove capture in the first ten minutes: make a trivial commit, then `git log -1 --format=%B` must show `Entire-Checkpoint: <id>` and `entire checkpoint list` must list it. If silent: run `claude` in the VS Code integrated terminal, or `entire session attach <id> --agent claude-code`.

Files created: `.entire/settings.json` and `.entire/.gitignore` (commit), `.entire/settings.local.json` (personal, gitignored), `.claude/settings.json` hooks (commit), `.entire/graph-agent.md` plus a managed block between `<!-- entire-graph:begin -->` and `<!-- entire-graph:end -->` in `AGENTS.md` and `CLAUDE.md` (commit; never edit the managed region; repo notes go outside the markers). Add a `.gitattributes` with `* text=auto` (inference: avoids CRLF noise in committed guides). Add a `.graphignore` for vendored or generated files that produce `E_FILE_TOO_LARGE` or `E_PARSE_ERROR`.

Windows pitfalls from the docs and inference: Git hooks may not find `entire` on PATH from VS Code Source Control until VS Code is restarted; if a UI commit skips hooks, run `entire configure --local --absolute-git-hook-path`. The link prompt cannot be answered from the UI, which is why `commit_linking` is `always`.

## 4. Privacy, because the repo is public

- Checkpoints store prompts, transcripts and metadata in the repo. **A key that appears in a prompt is a leaked key.** Keys stay in the environment or a gitignored `.env`, are never pasted into the chat, and a leaked one is rotated, not hidden.
- Consider `redaction.pii.enabled: true`. Review what is *not* redacted (images, `path` fields, raw session files). Drawings used as fixtures are the sample drawings from Storytopia (reuse approved), not a real child's work.
- Consider `entire configure --checkpoint-remote github:owner/repo` (same owner) to keep checkpoints in a separate repo, if we would rather not put transcripts in the code repo. The trade-off is judges cloning the code repo see no checkpoints; we choose the default (same repo) because the judges' access path is simpler.
- Write a one-line privacy note into `EVIDENCE.md`: what is public, whether PII redaction is on, that no real child data was used.

## 5. Commit structure: one intent, one commit, one checkpoint

A checkpoint is created per commit. The mapping from checkpoints to "agent improved" is only clean if commits are clean.

| Commit | Content | Notes |
| --- | --- | --- |
| 1 Enable | `.entire/`, `.claude/settings.json`, graph guide, `AGENTS.md`/`CLAUDE.md` block, `NOTICES.md`, `hackathon.md`, `docs/planning/` | Proves Entire was on from the first commit |
| 2 First oath | Contract module, deterministic verifiers, a fake tool log, no model yet | Entire was on before the interesting change |
| 3… Feature commits | One concern each | A fresh Claude session per task so each checkpoint maps to one intent |
| HR-001 baseline | The code that exhibited the failure (B0/B1 as it was) | The "before" |
| **HR-001 fix** | **Only** the fix: the prompt change and/or the verifier. No README edits, no refactors | The checkpoint in the video. Message includes the neatlogs trace ids (`before: tr_…`, `after: tr_…`) |
| HR-002, HR-003 fixes | Same discipline | |

Push directly or use merge commits. **Squash-merge, rebase and amend can lose or re-point the trailer.** Record the SHA, checkpoint id and trace id into the hardening record **immediately after committing**.

## 6. Using entire-graph while building

After `init-agents`, `CLAUDE.md` tells the coding agent to consult the graph before grepping. `--repo .` is required outside an Entire session. We keep command output as evidence.

| When | Command | Why |
| --- | --- | --- |
| Where does a commitment get verified? | `entire graph search --repo . --profile full --query "where a commitment verifies a scene"` | Ranked definitions with the call graph (`--profile full`; default is `fast`). Reads the working tree |
| Before editing a verifier | `entire graph impact --repo . --symbol <verifier symbol>` | Callers that break if the verdict shape changes (depth 2) |
| Before editing the scene node | `entire graph neighbors --repo . --symbol <scene node> --relation CALLS` | The node, its prompt and its guardrails as one neighbourhood |
| Before and after the fix | `entire graph verify --repo . --test "pytest tests/" --record-baseline base.json`, then `--pre-edit-baseline base.json` | A recorded before/after test outcome. Use a Windows path for the baseline file |
| After the fix commit | `entire graph diff --repo . --base <before-sha> --head <after-sha>` | The entity-level change: added verifier, changed prompt builder. A submission artefact. Note: committed tree vs working tree matters |
| Same commit | `entire graph checkpoint <id> --repo .` | Ties the diff to the checkpoint |
| A test fails | `entire graph explain` (failure text on stdin) | Declarations of the symbols named in the traceback |
| For an attachable map | `entire graph snapshot --repo . --format ndjson > graph.ndjson` | Reads the committed tree unless `--worktree`; run on a clean tree; keep the file out of git if large, put an excerpt in evidence |

Python, TypeScript and JavaScript are in the semantic tier with relationship analysis; run `graph capabilities --json` to confirm. It can miss dynamic or generated links, and a dirty indexable file disables cache reuse, so run on a clean tree. Do not run `entire graph stats` (the agent guide says not to). Graph output is evidence to check, not a conclusion; the agent opens the cited file before editing.

## 7. Evidence set and where a judge can open it

What a judge can verify with only a public GitHub clone:

- Commits with the `Entire-Checkpoint: <26-char id>` trailer.
- Checkpoint refs after `git fetch origin 'refs/entire/checkpoints/*:refs/entire/checkpoints/*'` then `git for-each-ref refs/entire/checkpoints/` (standard git; the fetch command is not documented by Entire).
- With the Entire CLI: `entire checkpoint explain --repo gh/OWNER/REPO <full-id>` (full id; auth requirements unspecified).
- entire.io: `https://entire.io/gh/<org>/<repo>/commit/<sha>` opens the commit page and its checkpoint. Sign-in is required for the owner. **Whether it renders anonymously is unknown; we test it in an incognito window.** A session can be set Public ("anyone with the link"), and transcripts download as Markdown or JSONL.
- Fallback layout: `entire enable … --checkpoint-backend branch` puts all checkpoints on the branch `entire/checkpoints/v1`, which a normal clone fetches (the trade-off: OPF redaction only applies on that backend; the Sentiment-Maxxers hackathon team used it).

Because we cannot be sure the refs reach the judge, **`entire graph` output and pasted CLI output are the primary artefacts; the refs are the confirmation.** Capture, into `evidence/entire/` and `EVIDENCE.md`:

- [ ] `entire version`, `git --version`, `entire graph version`
- [ ] `entire status --detailed`, `entire agent list`
- [ ] The enable commit sha
- [ ] For each key commit: sha, `Entire-Checkpoint` id, neatlogs trace id (the triple)
- [ ] `git log -1 --format=%B` showing the trailer, `entire checkpoint list`, and the first screen of `entire checkpoint explain <id> --full`
- [ ] `entire checkpoint tokens <id> --compare <baseline-id>`
- [ ] `entire graph checkpoint <id>`, `entire graph diff --base … --head …`, `graph verify` before and after, and a `graph snapshot` excerpt
- [ ] `entire why <path to the changed prompt>` (demo only; labs command)
- [ ] `git ls-remote origin 'refs/entire/checkpoints/*'` after push
- [ ] An entire.io commit URL, a screenshot, and the incognito-test result
- [ ] The privacy note (§4)

If a checkpoint push fails it only warns: watch the push output, run `git push` again, and check `entire status` for the pending count.

## 8. Beyond the minimum (use if time allows)

Context, iteration and verification evidence the judges may value (the Sentiment-Maxxers blog is the bar: 79 checkpoints, an intent-audit script in CI, a project overview, a demo):

- **Context:** `entire brain setup`, `brain brief "<task>"`, `brain remember "<rule>" --path X` (e.g. "never loosen a commitment"). Brain needs no login but sends session content to a model provider for fact extraction.
- **Iteration:** `entire recap --static` (hosted analysis, needs a push and a few minutes), `entire dispatch --local --since 2d`, `entire checkpoint tokens --compare`.
- **Verification:** `entire review general` (multi-agent verdict; configure with `entire review --configure …`), `graph verify`.

Skipped unless idle: `entire import` of unrelated old transcripts (would present pre-window work), mirrors and Entire-hosted repos (GitHub stays the public repo), cloud features that need an indexed repo.

## 9. What the video says about Entire (five points)

1. **Architecture:** Claude Code session → hooks → checkpoint linked to a commit; graph over the repo.
2. **Implementation:** hooks in `.claude/settings.json`, `commit_linking: always`, the trailer on the commit.
3. **Runtime:** the HR-001 fix commit's checkpoint, with the prompt, transcript and files; token numbers via `checkpoint tokens`.
4. **Reasoning:** `entire why` on the changed prompt shows the session that changed it **because of** that trace.
5. **Result:** `entire graph diff` showing the added verifier and the changed prompt builder; `graph verify` tests green after.

## 10. What we will not do

- Import old Cursor or Claude transcripts and present them as hackathon work.
- Treat a GitHub mirror as the submission.
- Edit `.entire/graph-agent.md`.
- Put a key, a real child's data or a private trace into any prompt that a checkpoint will store.
- Run `entire graph stats`.
