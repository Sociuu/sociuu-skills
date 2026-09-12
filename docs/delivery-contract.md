<!-- sociuu-delivery-contract: 2026-09-12.1 -->
# Sociuu delivery contract

Authoritative source: `Sociuu/sociuu-skills`, `docs/delivery-contract.md`.
Repository copies are synchronized release artifacts. Change shared rules at the
source; repository-specific product rules remain local.

## Scope and authority

Deliver the requested behavior with the simplest sufficient implementation.
Establish material decisions before adding recovery workflows, operation models
or frameworks. Report supporting work that would materially expand the task.

Identify affected producers, consumers and contracts; modify only required
repositories. Before writes load the repository instruction chain and use its
configured isolation provider. Canonical checkouts and other tasks' worktrees
are read-only discovery sources. Preserve unrelated state. Standalone clones
use their configured isolation workflow; a missing provider is a setup gap,
not permission to switch branches.

Humans merge and deploy. Production access and destructive shared-resource work
require their own authority and owning workflow. Implementation permission does
not grant those actions. Slack/email sends require explicit authorization.
Local tests, CI, staging and Production evidence are distinct.

## Task and implementation

Use `sociuu-task` for one canonical ClickUp task, Ledger and QA Runbook before
implementation. Small tasks may use named sections in one artifact; preserve
existing separate documents. Links & artefacts identifies current records and
participating MRs. Update at milestones, preserve concurrent edits and label
unsynchronized drafts. Do not log every tool call.

Read the QA Runbook before selecting checks. Map acceptance criteria and relevant
tenant, role, configuration and data cases to evidence. Extend concrete missing
scenarios instead of inventing an exhaustive matrix.

Routine understood work uses the host's coding tools with focused feedback.
Choose one diagnosis/implementation provider. CE Work may execute a substantial
plan in implementation-only mode; CE Debug may handle a difficult defect.
Selected TDD/design skills are techniques, not extra lifecycle owners. No
compulsory brainstorming, plan document or learning artifact for every task.

Delegate separable outcomes, independent review or worthwhile context containment.
Select capability/effort explicitly where supported. Give a focused brief,
required constraints and clear ownership. Return evidence and uncertainty;
validate integration without repeating every worker read. Report unavailable
capabilities. Personal model preferences stay outside team skills.

## Verification

`sociuu-verify` selects evidence and holds the pre-push gate. Use the cheapest
adequate lane for each criterion. One run may prove several criteria and is
recorded once. Independent checks may run concurrently without shared-resource
conflicts. Refresh only evidence invalidated by fixes or changed assumptions.

- Repository tests own local behavior. Apex uses `php artisan test:isolated` in
  its task worktree; do not start Dock solely for this lane.
- MyHub uses applicable live Playwright against task-bound Dock Apex and fixture
  tests for CI. Houston uses its configured Cypress stack. Inspect actual
  Fuse/Admin lane availability rather than assuming it.
- Update fixtures with changed contracts. Stubbed UI success is not live API or
  persistence acceptance. Data-dependent UI needs an API/persisted-state oracle
  where relevant. CI browser lanes use fixtures, not live APIs.
- Dock owns runtime/database lifecycle and exact source binding. Apex owns
  synthetic Scaffolding. Reuse matching verified environments/data; refresh when
  sources or scenarios invalidate them. Production data is never a prerequisite
  for local verification.
- Use `sociuu-before-and-after` for changes to numeric meaning, counts, rates,
  aggregates or migration/backfill outcomes. State applicability. Required
  `prod_read` comparison follows access authority, explains deltas and feeds
  synthetic shapes into Scaffolding. Missing comparison remains a gap but does
  not prevent independent synthetic tests.
- Use `sociuu-qa-guide` for economical human checks: real Dock URL, persona,
  setup, actions and expected outcomes. Human-only acceptance stays pending
  until executed. Supplemental guides do not invalidate adequate automated proof.
- AQ/CE Dogfood is opt-in: explicit request or accepted recommendation for a
  defined exploratory gap. It can complement Playwright. Standalone QA does not
  require building a new test framework first.

Report passed, failed, pending, not applicable with reason, or skipped with
explicit authority, bound to revision/environment. A lane can pass its assigned
criteria while the task is incomplete. Documentation-only work uses relevant
link, packaging, instruction-behavior and review checks, not product-browser QA.

## Review and publication

Complete two local reviews before push:

1. One independent repository review of exact diff, intent, standards and evidence.
   A supported native independent review or fresh reviewer covers correctness,
   tests and standards together. Add specialists for concrete uncovered risk.
   Deep CE review replaces this first review; do not stack review frameworks.
   Author self-review is not independent evidence.
2. `sociuu-coderabbit` against the isolation record's verified comparison base.
   Do not infer the base from the feature branch's upstream.

Triage findings: fix defects, reject unsupported scope expansions with reasons.
Refresh affected tests/review after fixes. Reproducible evidence may validate
findings; another opinion need not mean another team. Missing required reviewers
are gaps, not silent substitutions. Preserve separately required external reviews;
do not request duplicate forge bot reviews merely on publication.

Push/open the MR only after applicable verification, both reviews and required
human acceptance are complete and publication is authorized. Link task and
current evidence. An incomplete gate never licenses early push.

After human merge and verified staging proof, `sociuu-finalize` handles authorized
follow-through. Release runtime before eligible worktree cleanup. Preserve dirty,
unpushed, shared or active resources; no age-based cleanup.

For non-deployable documentation/instruction changes, record staging as not
applicable with a reason. Verified merge, applicable CI, packaging/link checks
and instruction-behavior evidence support finalization instead. Deployable
application changes retain their applicable staging proof.

## Skill selection

Explicit requests include ordinary language. Load skills for real triggers, not
because another checklist mentions them. AQ, deep review, interviews, prototypes,
panels and protected releases need their specific request or accepted scope.
Specialized tool prerequisites still apply. Use supported provider arguments;
no replacement GateHouse, receipt database or extra lifecycle service is required.
