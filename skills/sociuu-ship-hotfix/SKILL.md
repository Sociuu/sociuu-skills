---
name: sociuu-ship-hotfix
description: Enter Sociuu's protected Production hotfix procedure for an explicitly requested release, using the verified Apex release contracts for the affected repositories. Not for ordinary staging shipping.
disable-model-invocation: true
---

# Sociuu Ship Hotfix

Use only for an explicit Production hotfix request. This is a portable entrypoint,
not a second release engine. A skill invocation does not supply missing release
authority, credentials, or verification. Ordinary staging uses `sociuu-ship` and
`sociuu-finalize`.

Resolve the Apex checkout from the task's repository mapping and isolation
receipt. Verify its identity and read its applicable AGENTS.md. Do not guess a
developer path or use an unrelated task's checkout. Apex hosts the existing
protected release procedure for Apex, Fuse, Prime and coordinated releases.

Require and read these files from that verified checkout before any release action:

- `.agents/legacy/README.md`
- `.agents/legacy/sociuu-ship-hotfix/SKILL.md`

If either is missing, report that the selected Apex revision lacks the migrated
release provider. Do not fall back to a similarly named global staging skill or
reconstruct the release process. Select a compatible checkout through the task's
normal isolation workflow before continuing.

Follow the protected procedure and its exact local references and scripts.
Within it, legacy stage names resolve under `.agents/legacy/`; they are document
references, not global skill invocations. Review, readiness and publication use
their `references/protected-release.md` files. Production finalization uses
`.agents/legacy/sociuu-finalize/SKILL.md`, never shared staging finalization.

Preserve running-Production baseline checks, release-owner acknowledgement,
collision checks, exact tag authorization, Demo-before-Production verification,
human-performed merge-back, and coordination-window closure. Respect any narrower
action ceiling. Never infer rollback or destructive cleanup authority, weaken a
failed guard, or perform a merge on the user's behalf.

Return exact release identities, completed verification, remaining blockers and
the human actions required. Do not claim deployment or finalization from local
tests, a tag, or a merge alone.
