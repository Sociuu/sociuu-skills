# Sociuu Skills

Minimal, provider-neutral action skills for Sociuu engineering work.

Install them with the open skills CLI:

```bash
npx skills add Sociuu/sociuu-skills -g --skill '*' --agent codex claude-code
```

The catalog composes existing owners rather than replacing them: Compound
Engineering owns code work and browser dogfooding; Dock owns local runtime
lifecycle; Apex Scaffolding owns synthetic data; the forge and CI own delivery
evidence; humans own merge and deployment.

## Catalog and prerequisites

| Skill | Needs |
| --- | --- |
| sociuu-task | ClickUp task description and artifact/attachment access |
| sociuu-investigate | Relevant repository and evidence connectors |
| sociuu-verify | The repositories' own test tooling; Dock for the Playwright lane |
| sociuu-qa-guide | A running Dock environment for the task |
| sociuu-baseline | Apex checkout with the `prod_read` connection and its tunnel |
| sociuu-coderabbit | Authenticated CodeRabbit CLI (`coderabbit auth login`) |
| sociuu-resolve-git | Glab for GitLab; CE resolver and gh for GitHub |
| sociuu-aq | Dock skill/CLI, Apex Scaffolding, CE Dogfood and agent-browser |
| sociuu-finalize | Forge/CI and ClickUp; Dock/isolation for authorized cleanup |
| sociuu-ship | Forge/CI read access; human merge |
| sociuu-ship-hotfix | Explicit Production request; Apex's migrated protected release provider and its existing release prerequisites |
| sociuu-dock | Existing Dock-owned skill (compatibility entrypoint) |
| sociuu-task-isolation | Workspace-configured isolation provider |

## Delivery flow

Verification runs cheapest-lane-first: repository tests in the task worktree
(Apex's own test command, never through Dock), then Playwright against the local
Dock Apex, then the fixture-backed stubbed lane for CI, then a written human QA
guide, and only then AQ. AQ is opt-in and never automatic. Both the repository
code review and CodeRabbit run locally against the branch, and nothing is pushed
and no merge request is opened until the gate closes. `sociuu-verify` holds it.
Statistics and metrics changes add `sociuu-baseline`, whose findings are folded
back into Apex Scaffolding so synthetic data keeps mimicking Production.

The workspace's own `AGENTS.md` is the authoritative statement of that flow;
this catalog supplies the skills it routes to.

CE and Dock are installed separately. Scaffolding stays in Apex. Installation
does not install tools, grant access or provision an environment. Ordinary
ChatGPT/Claude web chats without filesystem/tool access cannot execute local
workflows; these are portable instructions, not a claim of identical host
capabilities.

For setup, follow the owning tools' installation and diagnostics: CE Setup for
CE configuration, the Dock installer/doctor for runtime tooling, and
agent-browser's installer for browser tooling. This package adds no separate
workstation setup workflow. Verify connector access with each developer's own
account. Re-run the installation command to refresh the selected skills.

The optional, explicit-only hotfix entrypoint requires Apex's migrated
`.agents/legacy/` release provider. Install it only alongside a compatible Apex
revision; it does not migrate repositories or grant Production authority.

Repositories must load their checked-in Sociuu delivery instructions through
AGENTS.md and CLAUDE.md. Those require the canonical ClickUp Ledger and QA
Runbook for every implementation task, even when QA is not applicable. Installing
skills alone does not establish that always-on repository policy.

The task description's **Links & artefacts** section is the required shared index.
Ledger and QA Runbook attachments are acceptable; identify current and superseded
versions. Native associations are optional, and ClickUp Docs are not required.
Preserve existing artifacts rather than migrating them just for presentation.

Resolve old project-local skills with the same names before adoption; do not
overwrite workspace isolation providers. Personal autonomy instructions remain
outside this catalog.
