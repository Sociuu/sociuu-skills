---
name: sociuu-investigate
description: Explain ambiguous Sociuu reports using code, configuration, tenant-scoped evidence and task history. Use to determine whether behavior is a defect, expected behavior, data/configuration state or an environment problem before choosing a fix.
---

# Sociuu Investigate

Establish expected versus observed behavior, environment, timeframe, affected
tenant/persona and source. Search relevant code, tests and existing tasks.
A report labelled bug is an observation, not proof of a defect.

Use the available first-party tools for relevant evidence. Keep client scope
explicit and output sanitized. Read-only Production investigation requires the
applicable repository and user authority; tool access alone does not authorize
new Production work. Do not require Production data for local reproduction.

Test competing explanations with the smallest useful checks. Use CE Debug for
technical diagnosis when appropriate, preserving the request's read-only ceiling.
Do not create tasks, modify configuration or send messages for an investigation-only
request. If local reproduction needs changes, use only authorized isolated setup.

Return the supported classification, cause/confidence, evidence, unknowns and
recommended action. Distinguish defect, expected behavior, configuration/data,
implementation gap, environment failure and unresolved evidence.

If the original request includes fixing the same issue, establish its ClickUp
record with Sociuu Task and continue to CE Debug for a confirmed defect or
CE Work for an approved implementation gap. Do not restart diagnosis or ask
whether to continue merely because the skill boundary changed.
