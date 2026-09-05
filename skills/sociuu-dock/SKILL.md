---
name: sociuu-dock
description: Compatibility entrypoint to the Dock-owned skill for preparing or inspecting a Sociuu local environment. Use when an existing workflow requests sociuu-dock.
---

# Sociuu Dock

Load and follow the installed `dock` skill maintained by the Dock repository.
Use its current command help and environment contract. This entrypoint carries
no separate runtime implementation or copied command procedure. If the owner
skill is missing, report the Dock setup prerequisite instead of guessing.

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
