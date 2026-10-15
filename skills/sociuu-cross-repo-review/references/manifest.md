# Review inputs

The manifest selects source, not permission to modify it. Use absolute Git
checkout or bare-cache paths and immutable commit IDs when available. Refs
are resolved once and their exact commits are retained in the receipt.

```json
{
  "version": 1,
  "intent": "Update the order response and its admin consumer together.",
  "repositories": [
    {"name": "api", "path": "/work/api", "base": "origin/main", "head": "HEAD", "role": "change"},
    {"name": "admin", "path": "/work/admin", "base": "origin/main", "head": "HEAD", "role": "change"},
    {"name": "portal", "path": "/work/portal", "base": "HEAD", "head": "HEAD", "role": "context"}
  ]
}
```

Each repository has a unique directory name. A context repository has equal
base and head commits: it is available to search but contributes no diff.
At least one change repository is required. Pin the consumer revision that
will actually run with the proposed producer, including companion branches
for coordinated work. Historical comparisons use contemporaneous source.

The output is a temporary combined Git repository, not a runnable platform.
Original application paths live beneath their repository names. Reviewers
read each repository's own instructions and resolve relative paths there.
The original source worktrees, indexes and refs remain untouched.

The receipt records resolved original revisions, synthetic base/head,
exclusions and the source manifest. Read its exclusions before claiming
coverage. Linked resources that were not materialized remain unavailable;
never silently substitute today's source for a pinned historical consumer.

Normal review uses CE's approved peer routing. If a participating repository
disallows external review, preserve that restriction in the combined review.
The benchmark profile disables external context lookup and the cross-model
route so that reference discussions and later source cannot leak into the
review. This restriction belongs to the benchmark, not CodeRabbit settings.
