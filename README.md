# Sociuu Skills

Provider-neutral action skills for Sociuu engineering. The
[delivery contract](docs/delivery-contract.md) owns acceptance and delivery rules;
[skill routing](docs/skill-routing.md) distinguishes conditional and explicit use.
Distribute version-stamped contract copies to repository
`docs/agents/sociuu-delivery.md`; each AGENTS.md/CLAUDE.md loads its local copy.
Standalone repositories do not depend on another developer's workspace path.

## Install

```sh
npx skills add Sociuu/sociuu-skills -g --skill '*' --agent codex claude-code
```

Install a reviewed source revision consistently across hosts. Check the installed
CLI's supported pin/ref syntax rather than inventing it. One source per skill;
preserve workspace isolation providers instead of replacing them with this
package's compatibility adapter. Validate resolved paths and missing dependencies.
Do not change active tasks' providers mid-run. Personal instructions/model aliases
stay outside this team package. Managed plugin caches are not edit targets.

## Catalog

| Skill | Needs / trigger |
| --- | --- |
| sociuu-task | ClickUp; implementation records and meaningful updates |
| sociuu-investigate | Read-only repository/tenant evidence; ambiguous reports |
| sociuu-verify | Product checks; select and reconcile acceptance evidence |
| sociuu-qa-guide | Exact Dock environment; economical human checks |
| sociuu-before-and-after | Authorized prod_read measurement; numeric changes |
| sociuu-coderabbit | Authenticated CLI; second local pre-push review |
| sociuu-resolve-git | Forge tools; authorized existing-feedback handling |
| sociuu-aq | Explicit QA; Dock, Apex Scaffolding, CE Dogfood, agent-browser |
| sociuu-finalize | Authorized post-staging reconciliation and cleanup |
| sociuu-ship | Explicit human merge handoff |
| sociuu-ship-hotfix | Explicit Production scope; existing protected Apex provider |
| sociuu-dock | Compatibility entrypoint to separately installed Dock owner |
| sociuu-task-isolation | Workspace-configured isolation provider |

CE and selected Matt Pocock skills are optional engineering providers. Routine
work does not require a full plugin lifecycle. Dock owns runtime/database state;
Apex owns synthetic Scaffolding; humans own merge/deployment. Install tools through
their owning setup workflows. Installation grants no access or runtime authority.
Hosts without filesystem/tools cannot execute local procedures and must say so.

Preserve existing ClickUp records and attachments. The Links & artefacts section
identifies current Ledger/QA records and participating MRs; native associations
and new ClickUp Docs are not requirements. Keep small tasks' records small.

## Validation

`python3 scripts/validate_catalog.py` checks skill metadata and relative links.
`python3 scripts/validate_catalog.py --repository PATH` also checks that a
repository's delivery copy exactly matches the authored contract. Run for each
changed distribution target. This checks packaging/drift, not agent behavior;
use the routing scenarios in docs/routing-scenarios.md for behavioral qualification.
