---
name: sociuu-task
description: Find, create and maintain the canonical Sociuu ClickUp task, Ledger and QA Runbook across repositories. Use before implementation and for task-document synchronization at milestones or handoff.
---

# Sociuu Task

Use the installed ClickUp connector, inspecting its current operations and fields.
Search by supplied task ID, source report, feature and existing MR links before
creating anything. Reuse a unique match; ask only when identity or scope conflicts.
Investigation-only requests do not authorize task mutations.

## Task and documents

Before implementation, establish scope, acceptance criteria, affected repositories,
source links and known unknowns. Preserve human descriptions and ownership.
Use explicit task routing first. Otherwise apply these Sociuu defaults in order:

- Houston work: Houston list `901816242128`.
- Roadmap initiatives, PRDs and broader planning: Sociuu App `900801780198`.
- Bugs, minor improvements and work up to two development days: Fixes & Bugs `900801780299`.
- Non-roadmap improvements over two development days: Enhancements `901816159903`.

Resolve uncertainty from scope and current list metadata; ask only if it remains
materially ambiguous. Query actual statuses and fields rather than guessing IDs.

Find the task's existing Ledger and QA Runbook. Create missing documents using
[task-documents.md](references/task-documents.md). They are canonical in ClickUp
for every implementation, bug, maintenance or infrastructure task. A QA Runbook
always exists, including explicit QA-not-applicable rationale and substitute
verification. Do not create an independent task ledger per repository.

Associate documents with the task through native Doc/task links. If task-parent
Doc creation is unsupported, create in the task's list and associate the Doc
through the supported relationship UI/API. A description/comment URL is only
a navigation aid, not a substitute for the requested native association.
Discover configured link fields/attachments for MRs, Figma and artifacts.
Do not invent relationship endpoints or claim an unsupported write succeeded.
Keep unresolved association work visible while continuing independent work.

## Maintain

Update at scope changes, meaningful implementation milestones, review, QA and
handoff. Keep status truthful; a published MR is not a staging release.
Read current content immediately before each update, preserve others' sections,
and refetch after writing. If another contributor changes an overlapping section,
reconcile or ask that owner; never replace it from a stale local copy.
Use append for discrete ledger entries where practical. Do not claim API locking
or concurrency guarantees that the connector does not provide.

Local Markdown required by CE is a working copy: include canonical page URL and
fetch revision/date, synchronize edits before handoff, and retain an explicit
unsynchronized flag when ClickUp is unavailable. Do not silently adopt two
authoritative versions. Migrate an existing repository ledger only after reading
its history and preserving its source link.

Link all participating MRs and relevant Figma, ADR, domain, test and QA artifacts.
Do not fabricate missing assets or require an ADR for a trivial task.
Return task/document URLs, synchronized state and concrete remaining gaps.
