---
name: sociuu-aq
description: Prepare task-bound Dock and Scaffolding prerequisites, then run Compound Engineering Dogfood as Sociuu's browser QA guard. Use only on an explicit QA request or an agreed recommendation; never as an automatic stage.
---

# Sociuu AQ

Sociuu AQ is a preflight and handoff, not a browser framework or a replacement
for Compound Engineering Dogfood. Dock owns the runtime; Apex Scaffolding owns
synthetic data; CE Dogfood owns diff analysis, journey mapping, browser QA,
small safe fixes, regression tests, commits, and its durable report.

## When AQ runs

AQ is opt-in. Run it when the user asks for it, or when `sociuu-verify`
recommended it for a surface no Playwright lane can reach and the user agreed.
Do not start it because implementation finished, because the change is
browser-visible, or because another skill's checklist mentions QA.

Browser exploration is the most expensive evidence Sociuu produces. Before
starting, confirm the cheaper lanes have already run and say what AQ will cover
that they could not. If a Playwright lane could reach the surface, build or
extend that lane instead; if the developer can verify it in a few steps, write
the guide with `sociuu-qa-guide`.

## Preflight

Read the canonical ClickUp QA Runbook and ledger before preparing any runtime.
Locate their current records through the task description's **Links & artefacts**
section; task attachments are acceptable and ClickUp Docs are not required.
If required documents are missing, use Sociuu Task. If browser/human QA is
explicitly not applicable, verify the rationale against the change, record the
alternative automated/operational checks and return without starting Dogfood.
Missing required QA capability is blocked, never not applicable.

Check that the runbook covers relevant tenant/role/configuration combinations
and defines independent API or persisted-state checks for data-dependent UI
outcomes. Distinguish live proof from mocks or route smoke checks. Fill concrete
gaps in the existing runbook; do not introduce another planning or QA stage.

1. Confirm the task-owned worktree and its exact environment binding through
   `sociuu-dock`.
2. Reuse a healthy current environment. If it is missing, stale, or mismatched,
   delegate preparation to Dock.
3. Check the runbook's required synthetic data and personas against current
   Scaffolding output. Read the Apex-local Scaffolding skill and module docs
   in Dock's bound Apex checkout. Reuse matching verified data; generate missing
   data or refresh only when justified and authorized. If coverage is missing,
   maintain the Apex blueprint/builders/verifier through the implementation
   owner and rerun verification. Never insert ad hoc rows or use Production
   data to conceal a missing scenario. Resolve missing applicability from task
   and code evidence; ask only if intent cannot be established.
4. Invoke `compound-engineering:ce-dogfood` directly in the prepared task
   worktree. Give it the existing Dock URL/port and declared personas or test
   context and current runbook; do not start a generic replacement server.
   Load CE's phase reference and report template, preserve its suite checkpoint,
   and use agent-browser for its browser work. In multi-repo tasks, provide all
   relevant diffs and the shared integration runbook; record each tested source
   and any coverage CE cannot execute. Do not claim a single-repo diff covers
   unexamined changes elsewhere.

## After Dogfood

Dogfood may make only its own permitted small, low-risk fixes. Its report is
browser-QA evidence, not merge or deployment authority. Any resulting source
change must follow normal product tests, CI, review, and human shipping steps.
Reconcile Dock's images/source after a fix before retesting browser behavior.
Link the resulting report, tested revisions, findings and limitations from the
ClickUp ledger. Synchronize any new runbook scenarios. Retain explicit skipped
or blocked scenarios; a completed report does not imply all acceptance passed.

Do not introduce GateHouse, a second QA state machine, a custom browser runner,
or a report-only wrapper around CE Dogfood unless a future pilot proves a
specific irreducible enforcement gap.
