---
name: sociuu-aq
description: Prepare task-bound Dock and Scaffolding prerequisites, then run Compound Engineering Dogfood directly as Sociuu's final browser QA guard. Use after implementation for browser-visible work or an explicit QA request.
---

# Sociuu AQ

Sociuu AQ is a preflight and handoff, not a browser framework or a replacement
for Compound Engineering Dogfood. Dock owns the runtime; Apex Scaffolding owns
synthetic data; CE Dogfood owns diff analysis, journey mapping, browser QA,
small safe fixes, regression tests, commits, and its durable report.

## Preflight

1. Confirm the task-owned worktree and its exact environment binding through
   `sociuu-dock`.
2. Reuse a healthy current environment. If it is missing, stale, or mismatched,
   delegate preparation to Dock.
3. Read the task's `scaffolding_impact` declaration. If it is `REQUIRED`, run
   and verify fresh Scaffolding through the selected Dock environment. If it is
   `NOT_APPLICABLE`, continue. If it is absent or ambiguous, stop rather than
   guessing from filenames.
4. Invoke `compound-engineering:ce-dogfood` directly in the prepared task
   worktree. Give it the existing Dock URL/port and declared personas or test
   context; do not start a generic replacement server.

## After Dogfood

Dogfood may make only its own permitted small, low-risk fixes. Its report is
browser-QA evidence, not merge or deployment authority. Any resulting source
change must follow normal product tests, CI, review, and human shipping steps.

Do not introduce GateHouse, a second QA state machine, a custom browser runner,
or a report-only wrapper around CE Dogfood unless a future pilot proves a
specific irreducible enforcement gap.
