# Setup status and what still needs your hands

Last updated 2026-10-10 12:30 IST. Secrets are never listed here; they live in `.env` (gitignored) and in `~/.aws`.

## Working now (verified with real calls)
| Tool | State | How to re-check |
| --- | --- | --- |
| neatlogs SDK + CLI + MCP | SDK 1.4.26 in `.venv`; CLI 0.2.0; probe trace written and read back through MCP | `.venv\Scripts\python -m neatlogs doctor --probe --json` (with `.env` loaded) |
| Entire | CLI 0.11.4, enabled for Claude Code, commit linking `always`, entire-graph 0.4.0 | `entire status --detailed`, `entire graph doctor --json` |
| Vertex AI (Gemini) | project `project-f0b6b4ce-541f-43ff-9f7`, location `global`; text, image and TTS verified | `gcloud auth print-access-token` + the calls in `hackathon.md` |
| K2 Horizon (judge) | `IFM/K2-Horizon-375B-A23B` at `https://api.ifm.ai/v1` | `curl $IFM_BASE_URL/models -H "Authorization: Bearer $IFM_API_KEY"` |
| AWS | profile `neathack`, us-east-1; **EC2/Lambda/IAM roles/ELB only, $25 cap, no Bedrock/Polly/S3** | `aws sts get-caller-identity --profile neathack` |
| Crustdata CLI | 0.2.19 installed, not logged in | `crustdata auth status` |

## Needs you (interactive steps I cannot do)
1. **Entire login**: `entire login` (browser) or `entire login --device`. Sign in at entire.io with GitHub and authorise the Entire GitHub App for the repo you will publish. Verify with `entire auth status`.
2. **Entire Trails**: submit the access form from https://hack.entire.io/neathacks-2026/ (it is feature-flagged; staff enable it manually). The page says a GitHub org admin imports the repo; for a personal repo you are the admin: test early whether import works.
3. **Publish the repo** (public, after kickoff): `gh repo create storybound --public --source . --push`. Then confirm `git ls-remote origin 'refs/entire/checkpoints/*'` shows checkpoint refs after the first commit.
4. **cfo.ai MCP**: start Claude Code from a shell that ran `. .\scripts\dev-shell.ps1`, run `/mcp`, select `cfoai`, Authenticate (browser). Then `list_orgs`, `inspect_skills` (build-model).
5. **Crustdata**: put the key in `.env` as `CRUSTDATA_API_KEY=...` and run `crustdata auth login --with-token < key.txt`, or authenticate the MCP server through `/mcp`. Free smoke test: `crustdata account credits --jq .account.credits`.
6. **Google ADC for the app**: `gcloud auth application-default login` (browser) and `gcloud auth application-default set-quota-project project-f0b6b4ce-541f-43ff-9f7`, so the Python SDK can call Vertex without a key file.
7. **neatlogs CLI login** (optional, for `neatlogs traces export` and sharing): `neatlogs profile set work --host https://app.neatlogs.com`, `neatlogs auth login`.
8. **Neatlogs trace sharing**: in the dashboard check whether a trace has a Share control, and test the public URL in a private window.

## How to start a session so everything is wired
```powershell
cd D:\storybound
. .\scripts\dev-shell.ps1 claude      # loads .env, then starts Claude Code here (hooks and MCP active)
```
Use the integrated terminal of VS Code or Cursor started the same way (`. .\scripts\dev-shell.ps1 code`), so `${NEATLOGS_API_KEY}` expands in the MCP configs.

## Rules that cannot be missed
- No commits before Sat 10 Oct 12:30 IST; commits only carry real dates.
- AWS: touch nothing that is not ours; one instance per user; stop what you start; $25 total.
- No real child's data in traces, the ledger, posts or the repo. Family demo only with a parent's consent.
- Crustdata data never enters the public repo.
