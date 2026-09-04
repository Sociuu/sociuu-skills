---
name: sociuu-symphony
description: Coordinate one bounded Sociuu delivery task through existing implementation, environment, QA, review, and human shipping owners. Use for approved implementation or confirmed fixes; not for read-only investigation or autonomous merge/deployment.
---

# Sociuu Symphony

Sociuu Symphony is a foreground delivery profile, not a service or control
plane. It coordinates one task in the current agent session and rehydrates from
the task worktree, forge, CI, test output, Scaffolding result, and Dogfood
report. Do not create a scheduler, database, webhook consumer, queue, or
separate lifecycle ledger.

## Flow

1. Preserve the user's authority, task scope, and repository boundaries.
2. Before the first product write, use `sociuu-task-isolation` for the exact
   write set.
3. Use Compound Engineering directly for implementation, debugging, review,
   commits, and ordinary code-quality work. Do not copy or wrap its workflow.
4. Run product-owned tests appropriate to the changed behavior and preserve CI
   as the delivery evidence owner.
5. For browser-visible work or an explicit QA request, invoke `sociuu-aq`.
6. Present the exact forge and CI state for human review. Invoke `sociuu-ship`
   only after an explicit shipping request.

## Foreground autonomy

Within the confirmed task scope, act as an accountable developer rather than a
step-by-step assistant. Continue through ordinary implementation, test, review,
environment, and QA decisions without asking for routine confirmation. Select
relevant tests, investigate failures, make small necessary repairs, reuse or
prepare a task-bound environment, and re-run affected proof when the evidence
shows it is needed.

Stop and request direction only for a material scope or product decision,
protected or destructive action, Production access, credentials or external
provider work, a dependency/lockfile change, an unverifiable result, or a
genuine conflict in authority. Report the evidence and the narrow decision
needed; do not turn ordinary engineering judgement into a handoff.

## Provider profiles

Use the same lifecycle on Codex, ChatGPT, and Claude. Adapt only invocation
syntax and capabilities. If the current host cannot use the required local
tools, environment, or forge integration, state the missing capability and
handoff; do not pretend another provider executed it.

## Boundaries

- Do not replace Dock, Apex Scaffolding, Compound Engineering, product tests,
  CI, or the forge.
- Do not auto-merge, deploy, finalize, delete worktrees, or perform protected
  actions without separately granted authority.
- Do not treat an agent narrative, a green local check, or a Dogfood report as
  evidence of merge, deployment, or production behavior.
