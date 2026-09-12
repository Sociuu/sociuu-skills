---
name: sociuu-before-and-after
description: Prove a Sociuu change moved the numbers it intended and nothing else, by measuring the same question before and after it on a deliberate client sample over the read-only prod_read replica, then folding what it reveals back into Apex Scaffolding. Consider it whenever a change can alter a statistic, metric, count, rate, aggregate, backfill or migration outcome.
---

# Sociuu Before and After

Compare numeric behavior on deliberate real-client shapes alongside synthetic
tests. Sampling can expose missed cases; it does not prove every possible input.
Read-only access follows the repository's Production authority. Local verification
must remain runnable with synthetic data when that access is unavailable.

## Decide whether it applies

This is not a stage every task runs. Judge it from the change itself, not from
the task's label, and say which way you decided and why.

Run it when the change can move a number a person or another system relies on:
statistics and dashboard figures, engagement or adoption metrics, counts and
rates, aggregation or scoreboard logic, a backfill, a data migration, or a fix
to how existing rows are interpreted. Retroactive changes are the strongest
signal — anything that alters what historical data *means* needs both readings.

Mark it not applicable when behavior cannot alter numeric outcomes, such as a
pure copy/style change. Classify endpoints, routing and configuration by actual
effects, not their labels. State the reason in one line.

Resolve unclear applicability from code and acceptance criteria; ask only when a
material product ambiguity remains. Do not query Production solely for ritual proof.

## Choose the sample

Pick clients deliberately, not by recency or size alone. A useful sample covers
the shapes the change must survive: a large active tenant, a small or new one,
one carrying legacy data from before the relevant schema or behavior change, and
any tenant the reported defect names. Four to eight clients is usually enough;
state why each was chosen.

## Measure

`prod_read` is a read-only replica reached through the jumphost tunnel. Use it
for measurement only. Never point local verification at it as a data source,
never copy rows out of it, and never let it substitute for Scaffolding.

Query from the Apex task worktree:

```sh
php artisan tinker --execute='...DB::connection("prod_read")->select(...)...'
```

Check the tunnel first with `lsof -nP -iTCP:3308 -sTCP:LISTEN`; it is usually
already open. Aggregate in the query. Do not select or print names, addresses,
message bodies or other personal fields — counts, sums, ratios and identifiers
are what this needs.

Capture the **before** numbers on the current behavior and keep the exact query
text alongside them, so the **after** run is the same question asked twice. Run
the after measurement against the changed code on the same sample, and present
the two side by side with the delta and an explanation for every client whose
number moved. An unexplained movement is an unfinished investigation, not noise.

Separate three outcomes: numbers that changed because the fix was right, numbers
that changed unexpectedly, and numbers that stayed wrong.

## Fold it back into Scaffolding

The point of looking at real data is that Scaffolding should not need to be
looked at again. When the comparison reveals a shape Scaffolding does not model
— a legacy row pattern, a null the code did not expect, a distribution that
breaks an aggregate — add it to the Apex Scaffolding blueprint, builders and
verifier so the next change meets it locally.

Model the data as it genuinely is, including the wrong-looking cases: Scaffolding
should mimic Production, not an idealised version of it. When a fix makes a
previously wrong shape correct, update Scaffolding in the same change and say
which case moved and why, so the synthetic data and the fix stay in step. Keep
every value synthetic; the shape is what transfers, never the content.

Record the sample, both measurements, the explained deltas and the Scaffolding
changes in the task ledger and QA Runbook, so the next change to the same figures
starts from this reading. This skill reads Production and writes nothing to it;
any Production change needs its own authority and workflow.
