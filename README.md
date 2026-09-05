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
| sociuu-resolve-git | Glab for GitLab; CE resolver and gh for GitHub |
| sociuu-aq | Dock skill/CLI, Apex Scaffolding, CE Dogfood and agent-browser |
| sociuu-finalize | Forge/CI and ClickUp; Dock/isolation for authorized cleanup |
| sociuu-ship | Forge/CI read access; human merge |
| sociuu-dock | Existing Dock-owned skill (compatibility entrypoint) |
| sociuu-task-isolation | Workspace-configured isolation provider |

CE and Dock are installed separately. Scaffolding stays in Apex. Installation
does not install tools, grant access or provision an environment. Ordinary
ChatGPT/Claude web chats without filesystem/tool access cannot execute local
workflows; these are portable instructions, not a claim of identical host
capabilities.

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
