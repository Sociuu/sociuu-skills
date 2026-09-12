---
name: sociuu-baseline
description: Measure Sociuu statistics or metrics behavior on a chosen client sample before and after a change using the read-only prod_read replica, and fold what it reveals back into Apex Scaffolding. Use for stats, metrics, aggregation, backfill or migration work.
---

# Sociuu Baseline

A statistics change is only verified against the data it will actually meet. A
green unit test proves the new formula computes; a before/after comparison on
real client shapes proves it computes the right thing, and shows which of the
old numbers were wrong on purpose.

`prod_read` is a read-only replica reached through the jumphost tunnel. Use it
for measurement only. Never point local verification at it as a data source,
never copy rows out of it, and never let it substitute for Scaffolding.

## Choose the sample

Pick clients deliberately, not by recency or size alone. A useful sample covers
the shapes the change must survive: a large active tenant, a small or new one,
one carrying legacy data from before the relevant schema or behavior change, and
any tenant the reported defect names. Four to eight clients is usually enough;
state why each was chosen.

## Measure

Query from the Apex task worktree:

```sh
php artisan tinker --execute='...DB::connection("prod_read")->select(...)...'
```

Check the tunnel first with `lsof -nP -iTCP:3308 -sTCP:LISTEN`; it is usually
already open. Aggregate in the query. Do not select or print names, addresses,
message bodies or other personal fields — counts, sums, ratios and identifiers
are what a baseline needs.

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
changes in the task ledger. This skill reads Production and writes nothing to
it; any Production change needs its own authority and workflow.
