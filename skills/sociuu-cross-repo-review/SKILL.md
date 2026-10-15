---
name: sociuu-cross-repo-review
description: Review coordinated Sociuu repository changes with CE against pinned producer and consumer revisions, or run a blinded historical reviewer comparison.
---

# Sociuu Cross-Repository Review

Review the revisions that will run together. CE remains the review provider;
this skill supplies a combined source snapshot and an independent integration
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
Source paths in findings include the repository directory prefix.

When at least two repositories change, or a changed contract has a consumer
in another repository, dispatch one fresh independent integration reviewer
with [integration-review.md](references/integration-review.md), the neutral
intent and the prepared tree/base/head. It examines interactions across
repositories; CE owns the ordinary review. Otherwise record why no additional
integration pass was needed.

Validate new integration findings against both sides of the contract. Merge
duplicates by cause and trigger, preserve unresolved material concerns, and
retain CE's receipt unchanged beside the combined result. Report findings,
source revisions, checks actually run, independence and coverage limits.
Static inspection does not establish live behavior. Fixing a source revision
requires a new snapshot and review of the affected changes.

## Historical comparison

For an explicitly requested blind comparison, read
[benchmark.md](references/benchmark.md) before selecting cases or exposing
reference findings. Use `prepare.py --blind`; the curator and reviewers have
separate contexts. Freeze the candidate before any holdout review, freeze
every result before unsealing the references, and report misses and invalid
references alongside matches. Keep source packets and labels private.
