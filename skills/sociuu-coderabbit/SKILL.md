---
name: sociuu-coderabbit
description: Run an explicitly requested local CodeRabbit opinion for a Sociuu branch against its verified base.
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

Run only when the developer explicitly requests CodeRabbit. It supplements the
required independent repository review and never blocks push or merge-request
creation. If authentication or the requested mode is unavailable, report that
result and continue the ordinary delivery gate. Do not opt into extra paid
credits unless authorized.

Evaluate findings against intent, source and repository rules. Fix defects; reject
unsupported rewrites or scope expansions with reasons. Report unrelated defects
separately. Refresh evidence affected by repairs, not unrelated checks.

Record command, reviewed base/head and dirty-state scope, dispositions and gaps
in the Ledger. Review output does not authorize push, approval, comments, merge
or deployment.
