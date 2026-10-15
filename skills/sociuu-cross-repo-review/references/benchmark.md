# Blind historical comparison

This compares a frozen candidate with source-validated historical findings.
It does not measure the production bug rate or prove parity from a small set.

## Curate privately

Use a separate curator context. Select cases before checking whether the
candidate succeeds. Record eligibility, exclusions and unavailable source.
Keep previously examined or tuning examples outside the holdout. Include
different repositories and risks, and changes with no CodeRabbit findings;
the latter are comparison controls, not proof of bug-free code.

For each reference finding, reconstruct the MR version present when the
comment was posted, verify the trigger in that source and inspect the later
correction. GitLab can move a diff note's recorded head to a later version:
`position.head_sha` alone does not establish finding-time source. Invalid or
unverifiable references remain in the accounting, with their reason.

Materialize original base/head snapshots and contemporaneous consumers.
Anonymized packet IDs and neutral feature intent go to reviewers. Keep MR
comments, discussion outcomes, later fixes, expected findings and answer
documents outside their view. Original Git history and remotes are withheld.
Read the preparation receipt's exclusions; retained source instructions can
still contain prior knowledge, so disclose that limitation.

## Freeze before review

Register the candidate files, review configuration and packet list with:

```sh
python3 scripts/benchmark.py register --directory RUN --candidate SKILL.md --candidate references/integration-review.md --cases CASES.json --reference-sha256 CURATOR_DIGEST
```

`CASES.json` is a list of objects with `id`, `tree`, `base` and `head`.
Candidate paths must include the implementation, prompts, selected CE version
and review/model configuration that can change the outcome. The curator
supplies an opaque SHA256 digest of the final reference file before review;
its contents remain withheld. Registration
records their hashes and each packet's tracked Git tree. An existing run is
immutable; a changed candidate starts a new run.

Use fresh reviewer contexts with only the frozen candidate, generic review
instructions and the assigned packet. The coordinator may know old findings;
it must not seed them into review briefs. Restrict reviewer reads to the
packet and provider assets. Without tool-enforced read isolation, call this
context blinding and disclose that it relies on the read boundary.

Run the skill's CE review and applicable integration pass. Preserve the CE
receipt and integrate validated findings into a JSON report. Record failed
reviewers and incomplete coverage; failure must not become a clean result.

```sh
python3 scripts/benchmark.py freeze --directory RUN --case case-01 --report REPORT.json --receipt ce=CE_REVIEW.json --receipt integration=INTEGRATION_REVIEW.json
```

Reports have `status`, `findings` and `integration_status`. A complete report
requires the raw CE receipt for this exact base/head and the integration
receipt when that pass ran. If no integration pass applied, use
`integration_status: not_applicable` with `integration_skip_reason`, and omit
the integration receipt. Each raw receipt is frozen and hashed beside the
combined report. Freeze failed/degraded outcomes too;
they count as incomplete coverage. Each freeze checks the candidate and
packet hashes, copies the output and records its digest. Packet admission
requires only the two synthetic commits, including unreachable objects, and
no remotes. Candidate directory symlinks are rejected; file targets, modes
and contents are part of the lock. Review output must
not modify tracked snapshot source.

Only after every case has a frozen result:

```sh
python3 scripts/benchmark.py unseal --directory RUN --expected PRIVATE_EXPECTED.json
```

The helper verifies all receipts and the preregistered reference digest before
copying references into the run.
The original reference file stays outside reviewer access until this point.

## Adjudicate and report

A separate judge checks frozen findings against the source and reference.
Match by causal defect and trigger, not wording or severity. Record each
reference as matched, missed, invalid or unresolved, with evidence. Classify
additional candidate findings as valid consequential findings, verification
gaps, noise or unresolved; an issue absent from CodeRabbit is not automatically
a false positive. Deduplicate repeated descriptions of the same cause.

Report the selected/attempted/completed counts, matches and misses, additional
valid findings, noise, coverage failures, wall time and recorded model usage.
State unavailable dollar costs rather than inventing them. Keep historical
overlap, live prospective performance and escaped defects separate. Never
tune on the holdout and report the rerun as independent validation.
