---
name: to-mockup
description: Create or revise a Sociuu UI mockup in the actual Fuse or Prime application, from a planning spec or a standalone idea, and render it for review before implementation.
---

# To Mockup

Turn the user's UI direction into a reviewable change in the owning application. Accept a PRD, planning conversation, ClickUp task, existing screen, or a brief idea as the starting point. The mockup is application code on an isolated task branch, shown in Dock; it is not a separate design app or a parallel copy of the product.

## Scope the design

Read the supplied context and the relevant repository instructions. Inspect the current screen and shared components before editing. Resolve only uncertainties that materially change the design; a short request does not require a full PRD or tickets. For a planning handoff, use the approved spec and relevant decisions as the design brief. If the mockup changes a product decision or acceptance criterion, record that change for the later ticket pass.

Use the workspace's task isolation and Dock instructions for the exact worktrees and runtime. Work in Fuse for legacy Admin or Prime for Houston/MyHub; use both only when the requested design crosses them. Keep the branch unmerged until the feature is implemented and verified.

## Build and review

- Start from the actual route and code when it exists. Reuse shared components and semantic styles; extend them when the design needs a reusable variant. Keep older screens in their current visual language unless the request includes their redesign. Record shared component or token changes that may affect other screens.
- Build enough of the real page or component to judge layout, interaction and relevant states. Use synthetic fixtures or mocked responses for data and backend behaviour, and make those substitutions clear to the implementer. Full API, persistence and business logic can wait for implementation.
- Render the change in the task's Dock environment. Inspect it at the sizes and states relevant to the request, iterate with the user, and capture representative screenshots. A Dock URL is a local review or screen-share surface; arrange a hosted preview only when remote viewers need a live link.

The `prototype` skill is optional for a narrow unresolved question. Its throwaway output does not replace the application mockup when the user asks for a design handoff.

## Handoff

For an exploration, return the rendered route, what the branch demonstrates, and any open design questions. Do not create planning documents or tickets merely because this skill ran.

For an approved implementation handoff, publish the design branch and give the implementer the GitLab branch **and exact approved commit** for each affected repository, the route or preview URL, screenshots, design decisions, shared component changes, and a clear list of simulated behaviour versus work left to implement. Attach screenshots and index these links in the owning ClickUp task after sign-off; link the later slice tickets back to that task. Reconcile the spec before publishing implementation-ready tickets when the approved mockup changed scope or interactions. If the user has not signed off, report the reviewable mockup and keep the handoff pending.
