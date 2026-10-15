# Behavior at input and persistence boundaries

Trace changed input through its actual caller, validation, transformation,
read and write. Inspect unchanged consumers and framework behavior needed to
establish the consequence. Apply these criteria to CE and the independent
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

## Strict parsing and selectors

Separate lexical shape from semantic validity. Date/time parsers may normalize
overflowing days or months, accept trailing text or apply a default timezone.
Numbers may be coerced, truncated or overflow. Trace accepted values into
cutoffs, ranges, tenant selectors and writes. Where invalid input must fail,
look for strict errors, range validation or a canonical round trip; a regex
alone may not prove validity. Show a concrete invalid input accepted by the
actual parser and the changed selection or write it causes. Distinguish an
intentional documented normalization from an accidental widened operation.

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
