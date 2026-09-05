---
name: sociuu-finalize
description: Complete Sociuu post-staging follow-through by reconciling merged MRs, staging evidence, ClickUp documents, release notes and eligible local cleanup. Use after staging release or to resume incomplete finalization.
---

# Sociuu Finalize

Inspect the canonical task and all participating MRs, merged source/target
revisions, post-merge pipelines and applicable staging deployment/verification.
A successful merge alone does not prove staging delivery. A partial multi-repo
release must remain partial.

## Task completion

If a task exists, refresh its Ledger and QA Runbook, actual QA/test reports,
all MR links, known Figma references and relevant repository artifacts.
Use Sociuu Task for document synchronization and native associations.
Ask only for a necessary artifact or identity that cannot be discovered;
mark absent optional designs/ADRs not applicable rather than inventing them.

Add or update one concise release-note comment keyed by merge/release identity.
State user impact, staging scope, MRs and evidence. Reuse existing matching
comments on retry. Set the list's verified DONE status only after all required
staging proof passes. Do not mark Production COMPLETE from staging evidence.

If no ClickUp task exists, report it and use Sociuu Task when the workflow
requires one; do not fabricate historical links or release evidence.

## Local cleanup and communication

Inspect task-owned Dock environments and worktrees, including other active
owners. Through Dock, remove only explicitly authorized task resources whose
evidence is retained; never broad Docker prune. Through the workspace's isolation
provider, remove only clean, inactive, preserved task worktrees after its delivery
checks and required cleanup authority. Retain dirty/unpushed/shared resources
and report why. Do not remove a checkout while an agent or process still uses it.

List outstanding Slack/email replies with source links and prepare drafts when
requested. Do not send messages without explicit authority. Report separate
release, task-document, communication and cleanup outcomes so cleanup pending
does not misrepresent a successful release.

This skill does not merge, deploy, roll back or change product code. Production
finalization stays with the separately authorized repository release procedure.
A staging pipeline may supply evidence; it cannot clean a developer's local
worktrees or impersonate their communications.
