---
name: sociuu-cross-repo-review
description: Review pinned Sociuu changes with CE across repository and input/persistence boundaries, prepare advisory MR reports, or run a blind historical comparison.
---

# Sociuu Cross-Repository Review

Review the revisions that will run together. CE remains the review provider;
this skill supplies a combined source snapshot and an independent contract
pass. Reports identify defects, verification gaps and unavailable coverage.
They grant no merge or deployment authority and do not change CodeRabbit.

## Prepare the review

Read [manifest.md](references/manifest.md). Resolve the participating change
and context repositories from the task, inspect their instruction chains,
and write the manifest. Include unchanged consumers of changed contracts.
Commit the intended source changes before snapshotting; uncommitted work is
outside this skill's input. Record an unavailable consumer as a coverage gap.

Run `python3 scripts/prepare.py MANIFEST.json --output NEW_DIRECTORY` from
this skill's directory. The helper reads the original repositories without
changing them. It creates a combined Git tree with a synthetic baseline and
proposed commit, and records the original revisions in `manifest.lock.json`.
Use the returned tree and baseline for every reviewer. A snapshot failure is
an incomplete review, not an empty finding set.

## Review and validate

Invoke `compound-engineering:ce-code-review mode:agent base:BASE_SHA` with
the prepared tree as its checkout. Follow CE's depth, independence, validation
and receipt rules. Discover the installed provider through the active skill
catalog; a missing provider is a blocker, not permission to approximate CE.
Give CE [behavior-review.md](references/behavior-review.md) with the neutral
intent; these are general review criteria, not a requirement to find a defect.
Source paths in findings include the repository directory prefix.

When at least two repositories change, a changed contract has a consumer in
another repository, changed input handling reaches persisted state or a
query/write selector, or authentication/return-URL/diagnostic credential handling
changes, dispatch one fresh independent contract reviewer
with [integration-review.md](references/integration-review.md), the neutral
intent and the prepared tree/base/head. It examines interactions across
repositories, local input/persistence boundaries and edited authentication,
return-URL or diagnostic credential flows; CE owns the ordinary review.
Producer and consumer may be in the same repository. Otherwise record
the specific reason no additional pass was needed. Keep `integration_status`
as the receipt field for this pass. For every new dossier use report version 2
and set `contract_review` to `{required:boolean, reason:string, evidence:[string]}`
from the examined source. Supply a specific reason and nonempty source evidence
whether the pass is required or inapplicable. Two or more changed repositories
always require the pass. A declared required pass cannot be skipped in a complete
report. Python checks this declaration's consistency, not the truth of the
reviewer's applicability judgment.

Validate new integration findings against both sides of the contract. Preserve
unresolved material concerns and retain CE/contract receipts unchanged. After
CE/contract source validation and before the final combined dossier, run the
mandatory fresh independent calibration in
[behavior-review.md](references/behavior-review.md) whenever candidate findings
remain. Give the worker only the pinned source and rating-hidden claim projection
specified there. Preserve its original JSON artifact and reconcile every input
with the original receipts using explicit dispositions, reclassifications and
causal merges. Failed or incomplete calibration keeps the dossier incomplete;
zero retained candidates skip the worker with an explicit reason in checks.
Report findings, source revisions, checks actually run, independence and coverage limits.
Static inspection does not establish live behavior. Fixing a source revision
requires a new snapshot and review of the affected changes.

## Prepare an advisory MR report

Read [mr-review.md](references/mr-review.md) for the report contract, configured
analyzers, QA Runbook, diagrams and GitLab integration. Keep plain explanations
and proposed tests separate from established findings and executed checks.
The rollout is advisory: do not create blocking discussions, commit statuses,
required checks or change CodeRabbit configuration. Publication requires an
authorized MR target; an inspection request alone does not authorize posting.

## Historical comparison

For an explicitly requested blind comparison, read
[benchmark.md](references/benchmark.md) before selecting cases or exposing
reference findings. Use `prepare.py --blind`; the curator and reviewers have
separate contexts. Freeze the candidate before any holdout review, freeze
every result before unsealing the references, and report misses and invalid
references alongside matches. Keep source packets and labels private.
