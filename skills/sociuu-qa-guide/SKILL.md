---
name: sociuu-qa-guide
description: Turn the task's QA Runbook into the exact steps a developer follows to verify a Sociuu change themselves in their Dock environment, with real URLs, sign-in, data and expected results. Use instead of AQ when the change is cheaply verifiable by hand.
---

# Sociuu QA Guide

Produce a guide a person can follow for economical human verification. Select it
for acceptance gaps or useful supplemental checks; AQ remains a separately agreed
exploratory option. Reuse the current runbook instead of creating another QA brief.

## Start from the QA Runbook

The QA Runbook is the input to this skill, not just a place to file the result.
Every Sociuu implementation task has one, written by whoever implemented the
change; it holds the acceptance criteria, the tenant/role/configuration
combinations that matter, and the scenarios earlier work on the same surface
already proved worth checking.

Read it before writing a single step. Locate it through the task description's
**Links & artefacts** section or its attachments, via `sociuu-task`. If it is
missing, use `sociuu-task` to establish it rather than inventing coverage from
the diff alone — a guide written without it will test what the change touched
instead of what the change has to satisfy.

Work from it in three passes:

- **Reuse.** Scenarios the runbook already defines become steps, in its terms.
  Do not re-derive or rename them; a scenario that reads the same across tasks
  is what makes regressions on this surface cheap to spot.
- **Fill.** Where the runbook is thinner than the change — a combination it does
  not cover, a data-dependent outcome with no independent check — extend it.
- **Feed back.** Any scenario this guide adds, and anything the developer's run
  discovers, goes back into the runbook through `sociuu-task`, so the next
  change to this surface starts further along.

Carry the runbook's acceptance criteria into the expected results verbatim where
they are already precise. Where they are vague, sharpen them here and update the
runbook with the sharper wording.

## Bind it to the real environment

Never write a placeholder URL, port, tenant or persona. Resolve them from the
running environment through `sociuu-dock`:

```sh
<sociuu> --environment "IDENTIFIER" status --json
```

Take the canonical MyHub, Fuse, Houston, Admin, Mailpit and Adminer URLs, the
client domain and the environment identifier from that output. If the
environment is not running, say so and give the exact command to start it rather
than guessing what it will be called.

State the exact revision under test for every repository in the environment, so
the guide cannot be followed against the wrong code later.

## Shape

1. **Environment** — identifier, repositories and revisions bound to it, the
   URL to open first, and whether Scaffolding was run.
2. **Sign in** — which persona, which tenant, how the credential is obtained.
   Magic links arrive in Mailpit; give the Mailpit URL rather than describing it.
3. **Steps** — numbered, one action each, naming the actual screen, control and
   input value. Include the setup a step depends on.
4. **Expected result** — what the developer should see, precise enough to fail
   on. When the outcome is data-dependent, add the independent check: the API
   response, the Adminer query, or the Mailpit message that proves it, so a
   correct-looking screen cannot pass a broken backend.
5. **Also check** — the regressions nearby that the change could plausibly break.
6. **Known gaps** — what this guide does not cover and what would cover it.

Cover the tenant, role and configuration combinations the change actually
affects. If a required persona or data shape is missing from Scaffolding, say
which one and treat it as an Apex Scaffolding gap, never as a reason to insert
rows by hand or to reach for Production data.

Store the finished guide and every scenario it added in the task's QA Runbook
through `sociuu-task`. Required human-only acceptance stays pending until the
developer reports the result, including failures/skips. If automated evidence
already proves the criteria, label the guide supplemental rather than making it
a new blocking gate. Guide production itself is not execution evidence.
