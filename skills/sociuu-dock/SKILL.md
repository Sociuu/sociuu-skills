---
name: sociuu-dock
description: Inspect, reuse, or prepare the exact task-bound Sociuu Dock environment through the installed sociUU command. Use when local runtime behavior, browser QA, or synthetic data needs an isolated environment.
---

# Sociuu Dock

Dock owns local runtime lifecycle: containers, URLs, databases, images, leases,
and cleanup. Use the installed `sociuu` command and its selected task
environment; do not operate Docker, Compose, databases, or volumes directly.

Reuse an environment only when its task/worktree binding, source identity, and
health are current. Otherwise ask Dock to create or prepare the correct
task-owned environment. Keep every command scoped to one explicit environment;
never infer a shared active environment or borrow another task's runtime.

Return the environment identity, applicable URLs, runtime health, and any
actionable blocker. Dock readiness alone is not product verification, merge
readiness, or deployment evidence.
