---
name: sociuu-task-isolation
description: Prepare one isolated Sociuu task worktree before product-repository writes. Use for implementation that changes one or more Sociuu repositories; not for read-only research.
---

# Sociuu Task Isolation

Before the first product-repository write, determine the exact repository write
set and create one task-owned worktree for each repository through the
workspace's configured isolation provider.

Require a stable task key, session or task ownership identity, and the intended
repositories. Use only the worktree paths recorded by the provider after it
returns a receipt.

Do not write in canonical checkouts, another task's worktree, a detached
checkout, or an unverified branch. Do not create ad-hoc worktrees to bypass a
failed provider. If the workspace has no configured isolation provider, stop
and request setup rather than guessing the branch or base.

This skill owns only isolation. Dock owns runtime setup; product repositories
own code and tests; the shared delivery contract selects implementation and
review providers.
