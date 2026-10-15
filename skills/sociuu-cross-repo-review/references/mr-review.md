# Advisory MR review

Review source before reading other bots' feedback when measuring independent
performance. Inspect open, closed and merged MRs as authorized; publication
is a separate action scoped to an authorized target. Keep historical answers
outside blind reviewer contexts.

## Explain the change

Write the report JSON in [report-contract.md](report-contract.md). Bind it to
the prepared manifest lock and account for every raw CE/contract finding,
including source-backed rejections. Never relabel an old review with new SHAs. Begin with
the concrete problem, what changes and what a user/operator will experience.
Use short sentences, define unfamiliar terms, and group the walkthrough by
behavior rather than one sentence per file. Do not paste commit messages as
the explanation. Retain exact source revisions and raw CE/contract receipts.

Each finding has severity, trigger, consequence, source evidence, suggested
correction and validation status. Explain what to change and why, then how to
prove the correction. Distinguish confirmed defects, unverified concerns and
verification gaps. Do not bury an unavailable review under a clean verdict.
Summaries, diagrams and polished prose do not establish review accuracy.
When the contract pass examined optional persisted values, summarize its
presence/clear matrix in the walkthrough or checks, including any unresolved
operation semantics. Label retained existing behavior explicitly and explain
whether it was introduced, extended or merely remains in the edited boundary.
An existing issue is not evidence of a newly introduced regression.

## Checks and documentation

Use `scripts/analyze.py` for configured ESLint or PHPStan in an exact, trusted
task checkout. The default plans without execution; `--run` explicitly permits
execution of repository tooling/configuration. Do not execute archived packet
code. No downloads, installs, automatic fixes or new dependency are implicit.
Import analyzer diagnostics as candidates for source validation, not confirmed
material findings. Keep command, exit, raw evidence and source provenance.

Check the repository's actual tooling first. A PHPStan entry in a lockfile
does not establish a configured PHPStan/Larastan check. Existing Pint `--test`,
Rector dry-run and other repository-approved checks may be run separately in
the authorized runtime and recorded with evidence. Missing tools/configuration
are unavailable, not pass. Changed-file lint does not establish full type or
application correctness. Keep legacy Fuse checks outside its delivery gate.

Record documentation and tests as risk-based checks: changed public API/event
contracts need updated contract documentation; surprising invariants need an
explanation close to the code. A trivial private method does not require a
docstring merely to meet a percentage. For behavior changes, identify a focused
test covering the changed failure path and run it when the environment permits.
Do not substitute a coverage percentage for checking assertions and test scope.
Every check names its applicability, result and actual evidence. Advisory
`hold` means a material finding or required-check failure needs attention;
`incomplete` means evidence is insufficient. Neither changes GitLab merge rules.

## QA Runbook and diagrams

Give humans and agents the same reproducible runbook: task-bound environment,
exact URLs/routes or command, synthetic persona/data setup, ordered actions,
observable expected results, negative cases, evidence to capture and cleanup.
Use placeholders only for genuinely unavailable bindings and identify them as
setup gaps. Label steps proposed, partially run or verified; verified needs
recorded results. Generating a runbook is not running it.

Include a Mermaid sequence diagram when changed interactions/order matter.
Trace actual participants, requests, asynchronous callbacks and failures from
source. Include DBML only for changed schema/relationships, with actual columns,
types, keys and migration evidence. DBML stays a code block; GitLab does not
need a custom rendering service. Explain why each omitted diagram is irrelevant.

## GitLab adapter and activation

`scripts/gitlab.py inspect --project NAMESPACE/PROJECT --mr IID --output FILE`
collects current MR state, revision refs, all notes and diff metadata through
managed `glab api` authentication. `event --event WEBHOOK.json --output FILE`
resolves an MR webhook to the same intake; it does not trust event SHAs as live
state. These are read-only operations. For an MR snapshot, use `diff_refs.base_sha`
(the merge-base) as its review base and the current source head. The target tip
`start_sha` can differ; a custom review against a different base needs a new
correctly scoped snapshot before publication as this MR review. The agent uses that intake to resolve
the task's participating revisions and invoke this skill; one MR alone is not
proof that no companion change exists.

Render locally with `report.py --report REPORT.json --ce-receipt CE.json
--integration-receipt CONTRACT.json --manifest-lock MANIFEST_LOCK.json --output REVIEW.md`. The publication
adapter defaults to preview, verifies every project's current head/base and
refuses stale source or closed/merged targets. Explicit `--publish` writes
one ordinary non-resolvable note on the authorized MR, preserving its human
description. Pass the same `--manifest-lock` to `gitlab.py publish`; list every additional
changed MR using repeated `--companion NAMESPACE/PROJECT!IID`. It only updates
its own note with the exact managed header and reads back the result.
It creates no pipeline, commit status or blocking discussion. Keep complete
finding sections in that note; source paths/lines are explicit rather than
pretending they are validated diff anchors.

An unattended MR hook needs a trusted executor to invoke this skill on MR
open/update events, coalesce by current revision and publish after validation.
Run it outside the builds-only MR pipeline. Prepare its command, credential
scope, runtime/model budget, duplicate/stale handling and rollback before
requesting activation. No webhook, runner, project setting, protected check or
existing reviewer pilot is activated by these files. Future blocking rollout
requires a separate decision and measured precision/coverage; retain CodeRabbit
unchanged during comparison. There is no unlimited/free model usage promise.
