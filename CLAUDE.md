# Storybound: project rules for every coding session

Storybound is a children's (age 4-8) storybook agent for the neatHack hackathon (10-12 Oct 2026, submit Mon 12 Oct 19:00-23:55 IST). It writes an **oath** for each drawing and lesson, verifies every page against it before the child sees it, repairs pages that break it, and ships a **receipt**. The full plan lives in `docs/planning/` (DESIGN.md, neatlog.md, entire.md, cfo.md, frontend.md, pitch.md). Read DESIGN.md first.

## Hard rules (do not break these)
1. **All code is written between Sat 10 Oct 12:30 IST and Mon 12 Oct 23:55 IST.** Nothing is committed before the kickoff time. Commits must carry real dates; never backdate, never rewrite history to hide work.
2. **Secrets never enter git, prompts, logs, traces or screenshots.** Keys live in `.env` (gitignored) or the OS credential store. Never paste a key into a chat, a commit message, a trace attribute or a doc. If a key leaks, say so at once so it can be rotated.
3. **No real child's data in traces, the ledger, posts or the repo.** Test inputs are fixtures (see `fixtures/`). Family demo footage is allowed only with a parent's consent and never uses a surname, school or location; the child's face is not shown.
4. **No Google ADK.** Orchestration is LangGraph. The only module that imports neatlogs is `backend/oath/observer.py`-style observer code plus the app entry point; keep it that way.
5. **AWS limits (hackathon account):** us-east-1 only; only EC2, Lambda, IAM roles and load balancers; one EC2 instance per IAM user; EBS <= 50 GB; **total allowance $25**; other teams' resources are visible in the account and must never be touched; stop resources when done. There is **no Bedrock and no Polly** in this account. Models and speech come from other providers (see DESIGN.md, "Models").
6. **Crustdata data never goes into the public repo.** Only our own aggregated numbers, with Crustdata cited. Never send children's data or personal data of minors to Crustdata.

## What the judges score
The agent 30% · use of neatlogs, Entire and cfo.ai 25% · demo video 20% (≤ 3:00, each tool covered on architecture, implementation, runtime, reasoning, result) · building in public 15% · usefulness and originality 10% · evidence and verification: every claim backed by something a judge can check.

## The eight agent capabilities neatlogs should show
planning (break a goal into steps) · tool use (choose tools, supply inputs, handle responses) · state (across steps, runs and failures) · context (bring in what is relevant, leave out the rest) · execution (long tasks run to completion) · recovery (handle failures and surprises) · verification (check results) · iteration (each result chooses the next step). Every story run is one trace; spans show model and tool calls with inputs and responses, state changes, retries, failures, agent messages, latency, tokens and cost.

## Evidence discipline (do this as we go, not at the end)
- Every named run is appended to `evidence/ledger.jsonl` with: UTC and IST time, git sha, fixture, arm (B0 observe-only / B1 gated), prompt versions, neatlogs trace id, outcome, per-commitment verdicts, repairs, tokens, cost, latency.
- After every named run: export the trace (`neatlogs traces export <id> --format markdown` and `json`) into `evidence/traces/` **and** take a screenshot into `evidence/screens/` (name: `YYYYMMDD-HHMM-IST-<what>.png`). Free-plan traces expire; the repo must not depend on the dashboard.
- Keep `hackathon.md` (the neathack build log) current: after each work session append a dated entry: what ran, what failed, which trace proves it, only tests that actually ran.
- "Agent improved" evidence = a run before and a run after a change, with the numbers compared, the commit sha, the Entire checkpoint id and both trace ids. One commit per intent so each checkpoint maps to one change.
- A run where an action failed and the agent recovered must exist, with the trace.
- Build in public: every `#neatHack` post goes into `evidence/posts.md` (URL, time, what it shows).
- Entire: `commit_linking` is `always`. After each key commit record (sha, `Entire-Checkpoint` id, trace id). Start a fresh Claude session per task. Never edit `.entire/graph-agent.md` or the managed blocks below.
- cfo.ai: the model's cost-per-story input is replaced with a neatlogs measurement; keep the Version history screenshot.

## Working style
- Small commits, one intent each, messages that say why. Run tests before committing. No unrequested abstractions.
- Trace first: before fixing a failure, find it in neatlogs (MCP `search_traces` / `get_trace_context`), write the hypothesis in `hackathon.md`, then fix, then compare runs.
- Report outcomes faithfully: if a test fails or a step was skipped, say so.



<!-- entire-agent:begin -->
Read .entire/agent-guide.md for this repository's workflow, source inspection, and verification guidance.
@.entire/agent-guide.md
<!-- entire-agent:end -->
