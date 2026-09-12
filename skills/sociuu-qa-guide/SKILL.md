---
name: sociuu-qa-guide
description: Write the exact steps a developer follows to verify a Sociuu change themselves in their Dock environment, with real URLs, sign-in, data and expected results. Use instead of AQ when the change is cheaply verifiable by hand.
---

# Sociuu QA Guide

The output is a guide a person can follow without asking a follow-up question.
Producing it costs almost nothing; running a browser agent costs a great deal.
Write the guide by default and reserve `sociuu-aq` for surfaces no cheaper lane
can reach.

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

Keep the guide in the task's QA Runbook through `sociuu-task` so the next change
to the same surface reuses it. A written guide is not evidence: the task is
verified when the developer reports the result, not when the guide is produced.
