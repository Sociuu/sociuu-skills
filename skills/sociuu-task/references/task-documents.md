# Task documents

Use existing task-linked Ledger and QA Runbook records or attach Markdown files
when records are missing. Do not create or require ClickUp Docs. Preserve existing
artifacts, including already-used Docs; no migration or deletion is required.
The main task description's **Links & artefacts** section identifies the current
records and distinguishes superseded attachment versions. Scale length to task
risk; headings are prompts, not reasons to manufacture content.

## Ledger

- Task, owner, scope, acceptance criteria and repositories.
- Current summary and completed/outstanding work.
- Decisions: alternatives, choice, rationale and useful discussion/source links.
- Implementation: relevant changes, all MR URLs and source revisions.
- Verification: commands/checks, expected and actual outcomes, tested revision
  and environment, report links, limitations.
- Release/follow-through: staging evidence, release-note text, cleanup,
  communication handoffs and remaining owners.

Maintain a readable current summary plus dated consequential updates.
Do not paste raw tool logs, secrets, customer rows or full chat transcripts.

## QA Runbook

- Canonical task, scope and expected behavior.
- Applicability: required, not applicable with reason, or blocked with missing
  capability. Never equate a missing environment with no QA requirement.
- Direct and indirect consumers, adjacent functions/pages, integration seams.
- Preconditions: exact Dock environment, synthetic data, personas and settings.
- Scenarios: normal, negative, edge, legacy, concurrency and recovery where
  relevant. Give concrete steps and expected UI/API/data outcomes.
- Automated/operational verification where browser/human QA is not useful.
- Exclusions, limitations and required external/human verification.

For a background job or cache change, explicitly consider consumer-visible
effects before declaring browser QA inapplicable. A documentation-only task may
use link, packaging and instruction-behavior checks instead of product-browser QA.

The implementer maintains the brief; human QA and CE Dogfood challenge it against
the actual change. Execution reports stay separate and are linked from the ledger.

## Multi-repository and milestones

One task spans all repositories and MRs. Parent documents cover overall acceptance
and integration. Add child documents for slices needing independent handoff;
link parent and child both ways. Do not duplicate whole parent requirements
into every child. A partial slice does not mark the parent DONE.
