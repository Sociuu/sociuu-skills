---
name: sociuu-ship
description: Reconcile a ready Sociuu merge request and present the exact human merge and post-merge verification handoff. Use only after an explicit shipping request; never merge or deploy autonomously.
---

# Sociuu Ship

Use this skill only when the user explicitly asks to ship or merge a Sociuu
task. Reconcile the exact MR, source SHA, target branch, current CI result,
required review state, and applicable local or QA evidence.

Present the exact human action required. A human performs the merge in the
forge. Afterward, observe the merged source and the post-merge pipeline before
reporting the outcome.

Never call a merge API, enable auto-merge, enter a merge queue, deploy, or
equate a green pipeline, Dogfood report, or agent approval with a completed
merge.
