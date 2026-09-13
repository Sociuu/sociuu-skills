<!-- sociuu-model-routing: 2026-09-13.1 -->
# Model routing

This is a capability policy, not a provider-specific price table. Each host maps
the roles to supported models and efforts. Read it before dispatching a worker.

| Role | Suitable outcomes | Coordinator retains |
| --- | --- | --- |
| Coordinator | Task framing, legacy behavior, acceptance, integration and final judgment | Every material decision and delivery claim |
| Evidence worker | Read-only source collection from Slack, Fireflies, Gmail, ClickUp, meeting notes, documentation, logs or targeted code navigation | Classification, recommendation and any external mutation |
| Bounded implementation worker | A named low-risk unit with specified behavior, files, tests and ownership; framework scaffolding and mechanical adjacent code | Schema/tenant meaning, data effects, contracts and integration |
| High-capability specialist | Statistics, metrics, authorization, tenancy, migration semantics, Actions, Jobs, queues, retries, external APIs and cross-repository contracts | Final delivery authority remains with coordinator |

Select the lowest capability that can complete the bounded outcome reliably. A
worker receives a compact brief with source paths/revisions, authority boundary,
owned files if it writes, expected evidence and a stop point. It returns facts or
changes plus uncertainty. The coordinator checks decisive evidence and actual
changes without recreating the worker's whole search.

Do not create a worker merely because there are several files. Keep a phase to
the smallest useful team, avoid overlapping write ownership and recursive teams,
and end workers after their outcome is integrated. Escalate once when a worker
finds ambiguity, missing evidence, conflicting sources, cross-boundary behavior
or material risk. Tool/connector access never authorizes messaging or mutation.

Provider mappings are personal/host configuration. For Codex, the current
recommended mapping is Astra for coordination and high-risk semantics, Sol for
specified implementation, Terra for read-only evidence collection, and Luna for
mechanical extraction. Hosts that cannot select per-worker models follow the same
boundaries using focused briefs and fewer workers.
