---
name: sociuu-verify
description: Select and run the verification lanes for a Sociuu implementation or bugfix, then hold the gate that must close before any push or merge request. Use after implementation and before delivery, in every repository.
---

# Sociuu Verify

This skill owns *which* verification runs and *in what order*. Dock owns the
runtime, product repositories own their tests, CE owns code review, CodeRabbit
owns its own review, humans own merge.

Two standing rules override convenience:

- **AQ is never automatic.** `sociuu-aq` runs only when the user asks for it, or
  when this skill recommends it and the user agrees. Browser exploration is the
  most expensive evidence Sociuu produces; spend it only where cheaper lanes
  cannot reach.
- **Nothing is pushed until the gate closes.** The branch stays local until every
  applicable lane has run and every finding is fixed or explicitly accepted. The
  merge request is created when confidence is highest, not when code compiles.

The task's QA Runbook defines what "verified" means for this change. Read it
through `sociuu-task` before choosing lanes: its acceptance criteria and its
tenant, role and configuration combinations decide which lanes are needed and
what each one has to assert. A lane that passes without satisfying the runbook
has not verified anything. Feed new scenarios and every lane result back into it.

## Lane selection

Pick every lane that applies. Record the ones that do not, with the reason.

| Lane | Applies when | How |
| --- | --- | --- |
| Repository tests | Always | In the task worktree, never through Dock. Apex: `php artisan test:isolated -- --filter=…`. Prime: `npm test`, `npm run e2e:myhub` (stubbed). Fuse: its own configured suite. |
| Playwright against local Dock Apex | The change is visible in MyHub, or in Fuse once its lane exists | First choice for behavioral proof. Prime: `npm run e2e:myhub:live:local`. Create or extend specs rather than skipping the lane. |
| Playwright stubbed | The change touches UI that CI must protect | `npm run e2e:myhub`. Update `e2e/fixtures/api/*.json` when the real contract moved — a fixture that no longer matches Apex is a defect, not a passing test. |
| Human QA guide | The developer can verify it in a few steps | `sociuu-qa-guide`. Default substitute for AQ on ordinary UI work. |
| Before/after comparison | The change can move a statistic, metric, count, rate, aggregate, backfill or migration outcome | `sociuu-before-and-after`. Not every task; decide from the change and state which way you decided. |
| AQ (`sociuu-aq`) | No Playwright lane can reach the surface — Fuse areas still without one, cross-surface journeys, exploratory risk | Only on request, or on an accepted recommendation. Say what it would cover that the other lanes cannot. |

Pipeline lanes never target a live API. CI runs the stubbed lane against the
fixture registry; the Dock-backed lane is a local and on-demand lane only.

## Gate order before push

Run in this order and do not skip forward:

1. Repository tests for every repository in the write set.
2. The applicable Playwright lane, including new or updated specs.
3. Before/after comparison, when the change can move a number.
4. Human QA guide produced, or AQ completed when it was agreed.
5. Code review of the change: `compound-engineering:ce-code-review`.
6. `sociuu-coderabbit`, last review before the merge request.
7. Fix everything found in 1–6, then re-run whatever the fix invalidated.
8. Only now push the branch and open the merge request.

A fix inside the gate reopens the lanes it could have broken. A fix that touches
application behavior reopens the Playwright lane; a fix that touches data or
aggregation reopens the before/after comparison.

## Report

Return one table of every lane with `passed`, `failed`, `not applicable` plus
reason, or `skipped` plus who authorized it, bound to the exact revision and
environment observed. Record the same in the ClickUp ledger through
`sociuu-task`. Never present a stubbed run, a green pipeline or a code review as
acceptance of behavior. An incomplete gate is reported as incomplete; it is not
a reason to push early.
