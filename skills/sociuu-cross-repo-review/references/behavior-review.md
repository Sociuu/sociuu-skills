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

- P0 needs a source-supported urgent, broadly destructive or unavailable path.
- P1 needs a consequential loss, exposure or broken core operation with a
  concrete reachable trigger; explain the affected users/data and recovery.
- P2 covers scoped functional failures and credible recovery/compatibility risks
  whose consequences do not establish the broader P1 impact.
- P3 covers limited presentation/diagnostic effects and speculative performance
  impact without a supported material workload or failure consequence.

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
