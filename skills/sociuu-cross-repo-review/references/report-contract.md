# Advisory report input contract

This is the interface for report.py, analyzer result import and GitLab publication. A combined source-review JSON can carry these presentation fields in addition to its original CE/integration metadata. Preserve raw CE and integration receipts separately.

Required top-level fields for an MR dossier:

- `version`: integer 3 for new dossiers. Versions 1 and 2 remain readable for historical evidence; known material holds still hold, while an otherwise clean recommendation is incomplete. Explicit GitLab publication requires v3. Preserve historical artifacts unchanged; their version cannot claim v3 closure coverage.
- `status`: complete, degraded or failed.
- `source_scope`: object with full Git `base` and `head_sha` of the composite snapshot.
- `repositories`: nonempty array `{name, base, head, role}`. Names are unique safe directory names; commits are full SHA1 or SHA256; role change/context; a context has equal revisions. Optional `project` is GitLab namespace/project, for publication mapping. At least one changed repo.
- `intent`: nonempty string describing desired behavior.
- `summary`: object `{problem, change, effect}` of nonempty plain-language strings.
- `walkthrough`: array `{repository, paths:[string], change, effect}`.
- `findings`: array `{id, title, severity, repository, path, line, trigger, consequence, evidence:[string], suggested_correction, validation_status, materiality, origin}`. Severity P0/P1/P2/P3; positive one-based line; repository must be listed; path repository-relative and no traversal/absolute path. validation_status confirmed/unresolved; materiality consequential/verification_gap/low_value/unresolved. origin CE/integration/both/analyzer. IDs unique within report. Confirmed material findings must have trigger, consequence and nonempty source evidence. Do not treat analyzer output as confirmed solely because a tool emitted it.
- `finding_dispositions`: array `{stage, source_id, action, reason, evidence, finding_id?}`. stage ce/integration/inventory/analyzer; source_id string normalizes original CE `#` (string/integer), integration finding `id`, inventory concern `id`, or original analyzer candidate `id`; action retained/rejected/reclassified; reason nonempty. Every finding and inventoried concern in each supplied receipt is accounted for exactly once. Retained maps to an existing report finding ID and permits many-to-one deduplication. Rejected requires source evidence, has no finding_id, and remains visible in the report. Changing raw severity, validation status or consequential materiality requires explicit reclassified action with reason and source evidence; its original severity and decision remain visible. A material issue cannot silently become a low-value passing item. Reclassified retains a finding_id just like retained. Complete CE/integration/both-origin findings need the corresponding retained receipt provenance; inventory concerns establish integration provenance; analyzer-origin findings need an analyzer disposition. Missing, unknown or duplicate dispositions are invalid. Unlinked candidates may remain in degraded outcomes when final receipts are unavailable, with explicit coverage limits.
- `checks`: array `{id, name, status, required, reason, evidence:[string]}`. Status pass/fail/warning/unavailable/not_applicable; required boolean. Pass needs nonempty evidence. A skipped/unavailable check is not pass. Documentation is a check with a specific applicability reason and source evidence; do not impose blanket docstring percentages.
- `qa_runbook`: object `{setup:[string], steps:[{action, expected, evidence_to_capture}], negative_cases:[same shape], cleanup:[string], execution_status, results:[string]}`. execution_status proposed/partially_run/verified; verified requires nonempty results. Complete reports require at least one concrete QA step. Steps are actual URLs/routes, synthetic setup and observable expected results, not 'test the feature'. Content supplied by agent, not generated from filenames by Python.
- `diagrams`: array `{kind, title, source, evidence:[string]}`. kind sequence/dbml; sequence rendered as Mermaid, dbml rendered as DBML code; each diagram needs source evidence. Empty allowed when not relevant.
- `diagram_notes`: object with nonempty reasons `sequence` and `dbml` describing applicability, including when omitted. Do not fabricate schema changes or diagrams for unchanged DB.
- `coverage_limits`: array of nonempty strings; empty allowed only when no stated limitation.
- `integration_status`: complete/degraded/failed/not_applicable; when not_applicable, nonempty `integration_skip_reason`.
- `contract_review` (v2/v3): `{required:boolean, reason:string, evidence:[string]}`. The reason and source evidence are nonempty. The reviewer decides semantic applicability from the edited source: two or more changed repositories always require the pass; one repository also requires it for a changed contract consumer, input to persistence or a query/write selector, or authentication/return-URL/diagnostic credential handling. `required:true` forbids `not_applicable`; an actual skip requires `required:false` and a specific skip reason. An optional pass may run voluntarily, and its failed/degraded state remains visible. A required pass may be degraded/failed only in an incomplete dossier. Structural validation cannot authenticate the reviewer's applicability claim or the truth of its source evidence.

For v3, complete original integration receipts additionally require
`inventory_concerns:[...]`. Each concern uses the report finding fields except
`origin`: unique nonempty `id`, `title`, P0-P3 `severity`, listed `repository`,
repository-relative `path`, positive `line`, `trigger`, `consequence`, nonempty
`evidence:[string]`, `suggested_correction`, `validation_status` and `materiality`.
All text fields are nonempty. These are source claims, not automatic final
findings. Every row in `boundary_checks`, `credential_policy_matrix` and any
`optional_field_matrix` includes `concern_ids:[string]`. IDs resolve to
`inventory_concerns`; a row has no duplicate references and every concern has at
least one row link. Multiple rows may reference one concern. With no concern,
use `concern_ids:[]` and source-backed no-concern reasoning in the existing row
result/evidence. The coordinator semantically audits every inventory before
projection or skip. A supported or credible unresolved failure enters source
validation and calibration even if the original `findings` list is empty.

When present in v3, `optional_field_matrix` uses `{rows:[...]}` with row fields
`field_group`, `saved_input`, `omitted_result`, `explicit_clear_result`,
`caller_evidence:[string]`, `evidence:[string]`, `base_head_attribution` and
`concern_ids:[string]`. All text/evidence fields are nonempty. Empty uses the
same source-evidenced not-applicable shape as the other inventories below.

For v3, `checks` contains exactly one `id:calibration` check. Every raw CE
finding, integration finding, inventory concern and supplied original analyzer
candidate enters the existing rating-hidden calibration, including claims
proposed for rejection. Input IDs are `ce/<original #>`,
`integration/<original id>`, `inventory/<original concern id>`, and
`analyzer/<original candidate id>`. The required check passes only with the supplied original
`calibration_receipt` matching `source_scope`, `status:complete` and exactly-once
group coverage of all these IDs. Its original JSON uses
`groups:[{input_ids:[string], severity, finding_type, validation_status, actor,
preconditions:[string], final_effect, recovery, evidence:[string],
missing_evidence:[string]}]` as defined in behavior-review.md. Input IDs and
source evidence are nonempty; actor/final_effect/recovery are nonempty text;
preconditions are a nonempty string list, and unresolved claims require nonempty
missing evidence. Each causal group maps to at most one final finding. A
source-backed rejected disposition stays visible; changed severity, validation
or materiality versus source or calibration requires explicit reclassification
with source evidence. A calibration-rejected claim can be retained only with
that explicit disagreement. No finding is forced merely to satisfy accounting.

Zero raw findings, zero inventoried concerns and zero final candidates permit a
worker skip with `status:not_applicable`, `required:false`, a specific reason
and nonempty source evidence. Zero final findings alone never permits skipping.
Degraded/failed calibration or absent required receipt can appear only with
incomplete review status, explicit coverage limits and a nonpassing check. It
cannot earn a clean result by removing final findings. Pass requires original
receipt evidence, not a check declaration alone. Partial calibration artifacts
may cover only completed inputs, with their incomplete status preserved.

When analyzer diagnostics are imported, preserve a separate original
`analyzer_receipt:{scope:{base,head_sha}, status, findings:[...]}` before
calibration. `findings` uses the same source-claim fields as inventory concerns,
with unique stable IDs across tools/repositories. Keep the raw tool artifact and
original repository revisions in source evidence. Tool error/warning labels are
not P0-P3 impact grades; assess the candidate against source and retain uncertainty.
This receipt represents the imported candidate collection, not proof a tool ran
or that its diagnostics are valid. Supply it as the optional sixth API argument
or `--analyzer-receipt` to rendering/publication. A supplied incomplete receipt
cannot support a complete report. With no imported candidates, omit the receipt.

Every original analyzer ID receives a `stage:analyzer` disposition and enters
calibration as `analyzer/<original candidate id>`, even if rejected or merged
into a CE/integration finding. Derive expected IDs from this unchanged collection,
not surviving final findings. Rejection may leave no final finding; original
calibration groups and source candidates remain unchanged and rendered through
their dispositions. Apply the same explicit reclassification and causal-merge
rules as other sources. A CE/analyzer-only merged finding may retain CE origin;
the analyzer identity remains visible in its own disposition.

Keep exact rating-hidden projections, original calibration JSON, worker/context
provenance, pinned scope and unchanged raw CE/contract receipts for inspection.
The helper verifies declarations, links and group accounting; it cannot prove
that inventory prose contains no undeclared concern, that source evidence is
true, that ratings were hidden or that independence was real. These require
source review and behavioral evaluation, not a prose parser or severity
classifier. Historical v2 findings/checks retain their older structural contract;
they cannot claim this closure coverage or publish through the current adapter.

Every report requires the original `prepare.py` snapshot receipt as a separate `manifest_lock` argument: its version, composite base/head and all original repository name/base/head/role values must match the dossier. Checkout paths remain private and are not rendered. This prevents accidental stale-source relabelling; it does not authenticate arbitrary files supplied by a malicious caller.

Every v2/v3 receipt claimed as a complete integration pass must match the report scope and carry valid findings and both inventories, even when the overall dossier is degraded. Malformed complete evidence is invalid.

Complete status requires supplied original CE receipt matching source_scope, status complete, nonempty reviewers and valid depth lite/focused/full; when integration_status complete its supplied receipt must have same scope and complete status/findings. A v2/v3 complete integration receipt must also contain `boundary_checks` and `credential_policy_matrix`, each as `{rows:[...]}`. A nonempty `boundary_checks.rows` item has nonempty `input_branch`, `validation_transformation`, `destination`, `observed_result`, `base_head_attribution`, and `evidence:[string]`. A nonempty `credential_policy_matrix.rows` item has nonempty `representation`, `source`, `transformation`, `destination`, `policy`, `observed_result`, `base_head_attribution`, and `evidence:[string]`. If an inventory has no applicable boundary or credential flow, use `{rows:[], not_applicable_reason:string, not_applicable_evidence:[string]}` with a specific reason and nonempty source evidence. Do not combine rows with a not-applicable claim. These inventories are rendered in v2/v3 dossiers. Complete receipts require findings arrays with unique original IDs. A failed/skipped/degraded provider receipt without scope can support only an incomplete dossier with no attributed raw findings; do not invent or rewrite its scope. Two or more changed repositories cannot skip the independent contract pass; complete reports cannot claim a degraded/failed required stage. These receipts are arguments to validation/rendering; they need not be embedded in public output. Degraded reports may be rendered with explicit missing-stage coverage and cannot earn a clean recommendation.

Public API for `scripts/report.py`: `validate_report(report, ce_receipt=None, integration_receipt=None, manifest_lock=None, calibration_receipt=None, analyzer_receipt=None)` raises ValueError on invalid input; `recommendation(report, ce_receipt=None, integration_receipt=None, manifest_lock=None, calibration_receipt=None, analyzer_receipt=None)` returns `{status: pass|hold|incomplete, reasons:[string]}` after validation; `render_report(report, ce_receipt=None, integration_receipt=None, manifest_lock=None, calibration_receipt=None, analyzer_receipt=None)` returns Markdown with summary, walkthrough, advisory check results, documentation check when provided, QA Runbook, conditional diagrams, findings and scope/coverage. Validate before rendering. Expose a CLI taking `--report`, required `--manifest-lock` and `--output`, optional `--ce-receipt`, `--integration-receipt`, `--calibration-receipt` and `--analyzer-receipt`; no network or application execution. Do not call recommendation with a second independent validation that omits already verified receipt context. Either recommendation accepts receipts too or validation of content/evidence is factored safely; preserve public renderer semantics.

Recommendation holds for confirmed consequential P0-P2 findings or failed required checks. It is incomplete for degraded/failed review, required unavailable/warning/not_applicable checks, or material unresolved findings. Otherwise pass means no established advisory hold in supplied evidence; it is never a merge permission, guarantee or platform-enforced gate. Keep failed/warning checks and unassessed coverage visible. Advisory rendering never creates a pipeline status or a resolvable discussion.

Existing-behavior findings must say so in their title and include base/head evidence. Summarize the independent pass's optional-field matrix in walkthrough/check evidence; ambiguous omission semantics remain an unresolved verification gap.

Also summarize applicable boundary checks and credential-policy discrepancies from the independent pass. Each retained finding's evidence or disposition reason states the supported impact, preconditions and recovery used to select its severity under behavior-review.md. Documentation/testing absence alone is a verification gap; an established behavioral defect is a separate claim. A downstream transformation can narrow the final effect, and deployment/workload/browser assumptions remain explicit. Reclassification changes presentation only: retain original receipt bytes and show the original rating. These semantic judgments require source review; report.py validates structure and provenance, not whether an impact assessment is true.

Every Markdown report identifies the actual source revisions and whether QA was proposed or performed. Render all model/source strings as data: prevent arbitrary HTML/details/marker injection and GitLab quick actions. Do not allow a standalone `/merge`, `/approve`, `/rebase`, etc. from source/model text to execute when the Markdown is posted. Keep Mermaid/DBML as fenced data, guard fence termination, and preserve normal readable prose. The publication helper also rejects quick-action lines before any network mutation. No static renderer can establish the truth of a model's semantic finding; call that limitation out in documentation.
