---
name: sociuu-coderabbit
description: Run the second local review of a Sociuu branch against its verified base, after independent repository review and before push.
---

# Sociuu CodeRabbit

From each task-owned worktree, obtain the comparison base from the isolation
record and confirm it resolves to the intended target history. A feature branch's
upstream is not its comparison base. Never guess poc/main/master.

Inspect installed CLI help for supported local review/base options. Bind the
recorded base SHA using `--base-commit` when supported; otherwise use a verified
`--base` target ref and record its resolved SHA. Include task-owned uncommitted
changes using supported options when present; do not claim a committed-only review
covered them. Prefer a stable committed candidate.

Run after independent repository review, before push. If authentication or the
required mode is unavailable, use supported diagnostics and report the gap.
A forge review is not an equivalent local result. Do not opt into extra paid
credits unless authorized.

Evaluate findings against intent, source and repository rules. Fix defects; reject
unsupported rewrites or scope expansions with reasons. Report unrelated defects
separately. Refresh evidence affected by repairs, not unrelated checks.

Record command, reviewed base/head and dirty-state scope, dispositions and gaps
in the Ledger. Review output does not authorize push, approval, comments, merge
or deployment.
