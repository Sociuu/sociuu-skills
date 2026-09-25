# Task documents

Use existing task-linked Ledger and QA Runbook records or attach Markdown files
when records are missing. Do not create or require ClickUp Docs. Preserve existing
artifacts, including already-used Docs; no migration or deletion is required.
The main task description's **Links & artefacts** section identifies the current
records and distinguishes superseded attachment versions. Scale length to task
risk; headings are prompts, not reasons to manufacture content. A small task may
keep Ledger and QA Runbook as named sections of one canonical artifact. Preserve
existing separate records; do not migrate just for presentation.

## Ledger

- Task, owner, scope, acceptance criteria and repositories.
- Current summary and completed/outstanding work.
- Decisions: alternatives, choice, rationale and useful discussion/source links.
- Implementation: relevant changes, all MR URLs and source revisions.
- Verification: commands/checks, expected and actual outcomes, tested revision
  and environment, report links, limitations.
- Release/follow-through: staging evidence, release-note text, cleanup,
  communication handoffs and remaining owners. After merge, keep this section
  and the task status current: set the list's verified DONE status only once
  staging proof passes, post one release-note comment (user impact, MRs,
  evidence), and never mark COMPLETE from staging evidence alone. The
  developer's own instructions decide when this runs.

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

When roles, tenant settings, feature flags or data states interact, select a
small risk-based set of combinations, including relevant denial and empty states.
State intentional omissions rather than expanding to every possible combination.
For data-dependent outcomes, define the expected values or invariants before
checking results and pair visible UI with an independent API or persisted-state
check where relevant. A changed value alone is not proof of correctness.
Distinguish live integration evidence from mocked/component/route-smoke results.
Reuse valid evidence after fixes; refresh checks affected by the change and its
dependencies. The repository and developer instructions select the evidence;
do not add another provider's whole lifecycle to an already-proven lane.

## Multi-repository and milestones

One task spans all repositories and MRs. Parent documents cover overall acceptance
and integration. Add child documents for slices needing independent handoff;
link parent and child both ways. Do not duplicate whole parent requirements
into every child. A partial slice does not mark the parent DONE.
