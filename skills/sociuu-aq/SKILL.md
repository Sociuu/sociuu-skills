---
name: sociuu-aq
description: Prepare task-bound Dock and Scaffolding, then run CE Dogfood for explicitly requested or agreed exploratory QA. Never an automatic completion stage.
---

# Sociuu AQ

Run only on explicit request or an accepted recommendation identifying the
exploratory gap. A generic checklist does not authorize AQ. State the bounded
journeys/personas and reuse available evidence. Playwright can complement AQ;
standalone exploration need not build a new test framework or run unrelated lanes.

## Prepare

Read the canonical QA Runbook and Ledger through sociuu-task. Check applicable
tenant, role, configuration and synthetic data cases, plus independent API or
persisted-state assertions for data-dependent outcomes. Extend concrete gaps.
A missing required capability is blocked, not not-applicable.

1. Confirm task worktrees and exact environment binding through dock (or the
   sociuu-dock compatibility entrypoint). Reuse a healthy matching environment.
2. Check personas/scenarios against current Apex Scaffolding output. Read its
   owning skill/module documentation in the bound Apex checkout when setup must
   change. Reuse verified data; route missing synthetic coverage to that owner.
   Never insert ad hoc rows or use Production data to conceal a missing scenario.
3. Invoke compound-engineering:ce-dogfood directly with the existing Dock URL,
   runbook, personas and relevant repository diffs. Use its phase reference,
   checkpoint and report; agent-browser owns browser interaction. Do not start
   a generic replacement server or claim one repository diff covers others.

## Reconcile

Dogfood may perform its permitted small fixes. Any source change requires normal
product tests and affected review, and reconciliation of Dock images/source before
retesting. Record exact tested sources, report, findings and coverage gaps in the
Ledger; add new scenarios/results to the QA Runbook. Keep skipped and blocked
acceptance visible. A completed report is not proof that every criterion passed.

Dock owns runtime/database lifecycle; Apex owns synthetic data; CE owns exploration.
This skill grants no merge, deployment, Production or additional message authority.
It introduces no GateHouse, custom browser framework or second QA state machine.
