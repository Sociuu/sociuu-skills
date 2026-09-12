---
name: sociuu-coderabbit
description: Run the CodeRabbit CLI over a Sociuu task branch before the merge request exists and triage its findings. Use as the final review gate after the repository code review and before any push.
---

# Sociuu CodeRabbit

CodeRabbit reviews the local branch, so it runs *before* the push, not after the
merge request. It is a second independent reviewer, not a replacement for
`compound-engineering:ce-code-review`; run it after that review so it sees the
code as it will actually be proposed.

## Run it

From the task worktree, against the branch's real base:

```sh
coderabbit review --agent --base "$(git rev-parse --abbrev-ref '@{upstream}' 2>/dev/null || echo poc)"
```

Use the repository's staging branch as `--base` — Apex and Fuse target `poc`,
Prime targets `main`, Admin targets `master`. Confirm the base the task was cut
from rather than trusting the default; `sociuu-task-isolation` recorded it.

`--agent` emits structured findings. Add `--uncommitted --include-untracked`
only while the change is still uncommitted. Prefer reviewing committed work, so
the findings match what the merge request will contain.

Run each repository in the write set separately, from its own worktree.

If the CLI reports it is not authenticated or not ready, run `coderabbit doctor`
and report the prerequisite. Do not skip the gate silently and do not substitute
a different reviewer for it.

## Triage

Findings are evidence, not instructions. For each one, decide: fix, or reject
with a stated reason. Reject anything that contradicts the repository's
`AGENTS.md`, its established patterns, or the task's agreed scope — CodeRabbit
does not know Sociuu's tenancy, Scaffolding or contract rules.

Fixes made here re-enter the verification gate: re-run the tests and the
Playwright lane the fix could have broken before pushing. A finding that reveals
a product defect outside the task's scope is reported, not quietly absorbed.

Record the review outcome and every accepted or rejected finding in the task
ledger. Never let CodeRabbit approve, push, comment on a forge, or merge.
