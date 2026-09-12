---
name: sociuu-verify
description: Select acceptance evidence for a Sociuu change and reconcile the pre-push gate. Use before choosing checks and after implementation; reuse valid evidence.
---

# Sociuu Verify

Read the repository delivery contract and canonical QA Runbook. Map each criterion
to the smallest adequate lane and expected result. Include relevant tenant/role/
configuration cases; extend missing scenarios. A lane proves its assigned criteria,
not necessarily the whole task.

| Lane | Selection |
| --- | --- |
| Repository tests | Changed behavior/adjacent risks in task worktrees. Apex: `php artisan test:isolated -- --filter=…`. |
| Live browser tests | Applicable API/UI behavior. MyHub: `npm run e2e:myhub:live:local` against exact Dock binding. Houston uses Cypress; inspect other repositories' actual lanes. |
| Fixture browser tests | CI UI protection. MyHub: `npm run e2e:myhub`; update `e2e/fixtures/api/` with contracts. Count one run once. |
| Human QA | sociuu-qa-guide for economical remaining checks; distinguish supplemental from required pending acceptance. |
| Numeric comparison | sociuu-before-and-after when numeric outcomes can change; state applicability and follow access authority. |
| AQ | sociuu-aq only on explicit request or accepted recommendation for a defined exploratory gap. |
| Documentation/configuration | Relevant link, metadata, packaging and instruction-behavior checks; no product suite solely because files changed. |

Dock is for integrated proof. Reuse matching verified runtime/synthetic data;
refresh invalidated bindings/scenarios through owners. No Production data for local
verification; CI browser tests use fixtures. Independent checks may run concurrently
without resource conflicts. Preserve commands, revision, environment and result.
Fixes reopen affected, applicable evidence, not every lane.

## Close the gate

1. Reconcile required acceptance. A guide leaves human-only acceptance pending;
   supplemental checks do not block proven criteria.
2. Complete one independent repository review against exact diff, intent, standards
   and evidence. Native independent review or a fresh reviewer covers correctness,
   tests and standards. Add specialists only for concrete uncovered risk. Deep CE
   review replaces this pass rather than adding a third workflow.
3. Run sociuu-coderabbit as the second local review.
4. Fix retained findings or reject with reasons; refresh invalidated tests/review.
   No silent replacement for a required reviewer.
5. Push/open the MR only when this gate closes and publication is authorized.

Record passed, failed, pending, not applicable with reason, or skipped with authority
in the Ledger/QA Runbook. Fixtures, CI and review alone are not live acceptance.
Report an incomplete gate as incomplete.
