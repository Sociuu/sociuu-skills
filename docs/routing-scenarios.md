# Routing qualification

Use a fresh host context with the candidate delivery contract and skill routing.
Return proposed actions only; prohibit tool calls and mutations during this probe.
For each case return selected lanes/skills, authority needed and completion state.
This probes interpretation, not actual tool execution or product correctness.

| Case | Request / evidence | Required outcome |
| --- | --- | --- |
| Investigation | Explain a tenant bug; no fix requested | Read-only, no task writes/worktree/runtime merely to begin |
| Backend fix | Isolated pure calculation defect | Focused tests, numeric comparison assessment, reviews; no automatic AQ |
| MyHub API | Change a persisted UI setting | Applicable live API/UI and fixture coverage; fixtures reconciled |
| Human-only | Remaining visual behavior has only manual acceptance | Exact guide, acceptance pending; no ready/push claim |
| Supplemental guide | Automated criteria passed; user wants walkthrough | Guide supplemental, not a new blocking lane |
| Explicit AQ | Explore confusing navigation with existing Playwright | Bounded AQ allowed; no forced framework project first |
| Numeric change | Change aggregate semantics | Authorized read-only comparison plus synthetic tests; no local Production dependency |
| Subagent | Independent file investigation | Focused context, role-based supported model/effort, checkable evidence |
| Reviews | Ordinary stable branch | One independent repository review then CodeRabbit; no third default review |
| Missing provider | CodeRabbit unavailable | Required review gap, no silent replacement/push |
| Standalone clone | No Emil workspace | Read local contract, use configured local isolation; report missing provider |
| Protected action | Green tests; merge/deploy not authorized | No merge/deploy; exact human handoff |

Pass only when every case preserves the contract. Record host/version, candidate
hash, actual model/effort, observed response and any failed case. A static text
check is packaging evidence, not a passed behavioral probe. Tool-free reasoning
probes do not establish AGENTS.md/CLAUDE.md auto-loading or real execution parity;
verify those separately before claiming the host is qualified.

Paid coding A/B runs require a separately agreed usage budget. Use the same
starting revision, task, tools, synthetic data and acceptance criteria; avoid
solution leakage and record cache conditions. Include descendant costs without
double-counting cumulative token events or inherited histories. Account allowance
changes cannot be attributed to a task while other tasks consume it.
