# Behavior at input and persistence boundaries

Trace each edited entry point through its actual callers, input branches,
validation, transformation, reads and writes. Include retained branches of
that entry point and unchanged consumers needed to establish the consequence.
Apply these criteria to CE and the independent
contract pass; they are prompts for investigation, not findings by themselves.

## Presence and preservation

For each optional field in a partial update, distinguish absent, explicit
null, empty collection/string, false and zero. Follow defaults, filtering,
merging, serialization and mass assignment into the saved representation.
An omitted field generally preserves state only when the actual operation's
contract says so; replacement operations may intentionally clear it. Establish
that contract from callers, documented intent and existing tests before
objecting. Consider an existing nonempty value, an update to an unrelated
field, and an explicit request to clear the value. Verify the resulting value
in each path. Do not assume a UI always sends every persisted option.
When an edited write branch rebuilds persisted options, make a compact evidence
matrix for the affected optional fields or groups: saved nonempty value,
omitted request value, explicit clear, resulting saved value, caller path and
base-versus-head behavior. Record it even when no defect is retained. Tests
for an explicit empty value do not establish omission semantics. If the
operation's replacement-versus-patch contract cannot be established, state the
specific missing contract/test evidence instead of asserting preservation.

Do not lose an affected existing defect merely because CE correctly excludes
it from newly introduced regressions. In the independent contract pass, retain
a source-backed existing problem in an edited boundary as a separately labelled
existing-behavior finding when a reachable failure and intended contract are
established. If intent remains ambiguous, keep the concrete mismatch as an
unresolved verification gap. Include base/head evidence and do not claim the
MR introduced it. An edited command's retained explicit-selector branch is
in scope even when the new behavior concerns omitted input. Inspect sibling
branches feeding the same action, query or write, rather than only added lines.
This is bounded to edited entry points and their direct contracts and callers;
it is not permission for a repository-wide audit.

## Strict parsing and selectors

Separate lexical shape from semantic validity. Date/time parsers may normalize
overflowing days or months, accept trailing text or apply a default timezone.
Numbers may be coerced, truncated or overflow. Trace accepted values into
cutoffs, ranges, tenant selectors and writes. Where invalid input must fail,
look for strict errors, range validation or a canonical round trip; a regex
alone may not prove validity. Show a concrete invalid input accepted by the
actual parser and the changed selection or write it causes. Distinguish an
intentional documented normalization from an accidental widened operation.
Record the source-backed result for both explicit and omitted selectors when
an entry point supports both. A valid identifier after coercion does not prove
that the original input selected it intentionally. An existing failure belongs
in the independent contract result with its base/head attribution.

## Credential handling across representations

When authentication, return URLs or diagnostic capture change, trace the
credential policy through every representation that is accepted, forwarded,
stored or logged. Build a compact policy matrix: input component, decoding or
normalization, sensitive-key policy, validator/redactor, downstream destination
and evidence. Include retained paths through the edited flow. Compare the
project's declared sensitive-key set with each implementation and actual caller;
different handling needs a source-backed reason, not assumed equivalence.

Check whether validation inspects the entire value that is later forwarded.
URL query and fragment parsing, repeated delimiters, encoding and key spelling
can leave one component unchecked while another is accepted. Follow the actual
parser/router version and consumers before asserting a bypass. Trace diagnostic
arguments through redaction into console, test-failure output and artifacts;
test support code can be an output boundary. State where a sensitive value
could enter that path and distinguish a reachable exposure risk from an
observed leak. Record unassessed destinations explicitly.

## Evidence and intent

For every retained defect, give reachable input, affected caller, exact source
lines, transformation and observable consequence. Check schema constraints and
framework guarantees before claiming malformed stored data is reachable.
Compare the behavior with explicit requirements: deliberate failure caching,
compatibility exceptions and policy choices are not defects merely because a
different design is possible. If reachability or intended behavior is unknown,
keep that uncertainty visible; do not promote it to a confirmed material issue.
Recommend a focused test that distinguishes current behavior from the intended
one. Static source reasoning is not evidence that the test was executed.

## Severity and finding type

Assess severity after tracing the final observable effect, including downstream
validation, normalization, trimming, retries and recovery. Separate the defect's
existence, its impact and the conditions needed to reach that impact. State
those conditions and supporting source evidence in the finding or disposition.
An unknown production incidence does not negate a demonstrated causal failure.

Establish whether the trigger is a supported, valid operation or malformed or
unsupported input; passing an incomplete validator does not make a nonsensical
request a valid operation. Trace actor permissions, changes to persisted state,
jobs and external side effects, the final effect on other users or shared
resources, and practical recovery. A valid input that saves or returns a shape
excluded by its response contract is a compatibility defect even when no deployed
enforcing consumer is shown. State any conditional client failure separately.

- P0 needs a source-supported urgent, broadly destructive or unavailable path.
- P1 needs a consequential loss, exposure or broken core operation with a
  concrete reachable trigger; explain the affected users/data and recovery.
- P2 covers scoped functional failures and credible recovery/compatibility risks
  whose consequences do not establish the broader P1 impact.
- P3 covers limited presentation/diagnostic effects and speculative performance
  impact without a supported material workload or failure consequence. An
  isolated authenticated malformed request that fails before changing state,
  has no supported broader exposure and recovers by resubmitting valid input
  belongs here, including an uncontrolled error instead of validation feedback.

Invalid-input acceptance or an API error alone does not establish P2. Preserve
higher grades when source establishes resource exhaustion, unauthorized access,
persisted damage, broken valid operations or irreversible effects. A permitted
cancellation that leaves work dispatchable is assessed through the later work
and recovery, not merely its limited request shape or successful HTTP response.

Missing tests or documentation alone are verification gaps. Cite an applicable
requirement or a concrete unchecked failure, and report an actual defect
separately when established. Cosmetic consistency is low value. A count of
requests alone does not establish latency, rate-limit failure or an outage;
identify the reachable workload and any bounds. A mixed-version incompatibility
needs its deployment preconditions stated; absent deployment evidence is not
proof of a live outage. Unproved browser/data reachability stays explicit.

Choose the severity supported by the demonstrated consequence, rather than
the most damaging hypothetical extension. Preserve a credible unresolved
high-impact concern as unresolved with its missing evidence. Reclassification
must retain the original receipt, explain the change and remain visible; it
must not turn missing evidence into a clean review.

## Fresh independent calibration

After source validation, audit the inventory prose against its linked concerns:
every supported or credible unresolved failure must enter the projection,
including inventory-only claims and claims proposed for rejection. Missing
source closure is an explicit coverage limit, not a zero-candidate outcome.
Before writing the final dossier, dispatch the existing fresh calibration worker
for all raw CE findings, integration findings and inventory concerns, plus supplied original
analyzer candidates, including those proposed for rejection. Reuse this one calibration pass for their
combined source validation and impact assessment. Use a new context with no coordinator history or earlier review
ratings. Give it only the prepared tree path and pinned base/head, these generic
behavior, intent and severity criteria, and a claim projection containing stable
input IDs (`ce/<original #>`, `integration/<original id>`,
`inventory/<original concern id>`, or `analyzer/<original candidate id>`), title,
repository-prefixed path, line, reachable trigger, alleged
consequence and suggested correction. Strip explicit rating prefixes from
titles. Withhold original severity, validation, materiality, disposition and
rating rationale, raw receipts and coordinator history. Treat projected claims
as allegations to check against the source, not established findings.

The worker independently traces each claim to its final observable effect,
checks intent against source/callers/tests, groups claims sharing one causal
defect and assigns supported P0-P3, finding type and validation status. For every
input ID, return actor, preconditions, final effect, recovery and exact source
evidence, or the specific missing evidence. Apply the severity criteria above
without a blanket downgrade for data or security defects. Preserve credible
unresolved concerns, including high-impact risks whose reachability is uncertain.
Different wording or symptoms alone do not establish distinct defects; causal
merges must explain the shared source failure and account for all input IDs.

Return an original JSON artifact with `scope:{base,head_sha}`, overall
`status:complete|degraded|failed`, and `groups:[{input_ids, severity, finding_type,
validation_status, actor, preconditions, final_effect, recovery, evidence,
missing_evidence}]`. `input_ids` maps every projected ID exactly once, including
rejected or unresolved claims; `finding_type` is
`consequential|verification_gap|low_value|unresolved`, and `validation_status` is
`confirmed|unresolved|rejected`. Evidence gives source paths/lines and reasoning;
missing evidence stays explicit. A rejected claim still receives a supported
severity assessment of its alleged effect, with rejection explained in evidence.
Incomplete source coverage makes the artifact degraded/failed, not complete.
`actor`, `final_effect` and `recovery` are nonempty strings; `preconditions`
and `evidence` are nonempty string lists; `missing_evidence` is a string list,
nonempty for unresolved claims. Evidence supports rejection as well as retention.

The coordinator retains the exact projection, original worker JSON, worker
identity/context provenance and pinned source scope beside the unchanged raw
CE/contract and imported analyzer-candidate receipts. Reconcile all input groups against those receipts in the
existing `finding_dispositions` (`stage:inventory` for inventory concerns; `stage:analyzer` for analyzer candidates):
explain retained/rejected claims, record changed
ratings/types/validation as explicit reclassifications, and map causal duplicates
to one final finding while preserving every original source ID. Explain any
source-backed disagreement with calibration; never erase missing evidence or
uncertainty to obtain a clean result. A failed/incomplete calibration cannot
produce a complete dossier even if reconciliation removes every final finding.
Skip the worker only with zero raw findings, zero inventoried concerns and zero
final candidates after the semantic inventory audit. Record that exact reason
and source evidence in the nonrequired `calibration` check as `not_applicable`.

Record the calibration check and artifact evidence under report-contract.md.
A declaration and structural validation cannot authenticate semantic honesty,
source reasoning or actual independence; the original artifacts and provenance
are required for inspection. Calibration grants no publication or merge authority.
