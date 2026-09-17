---
name: sociuu-better-agent
description: Refactor a repository's AGENTS.md into concise, progressively disclosed agent instructions. Use when splitting or auditing repository guidance, especially into the Sociuu-style .agents/instructions tree.
---

# Refactor Agent Instructions

Make repository guidance easier for an agent to load just in time. Preserve
the instructions that affect decisions; do not turn a documentation cleanup
into a change to product behavior, delivery workflow, or personal settings.

This skill is for refactoring agent instructions, not for implementing a
product task. Keep existing repository-specific authority and nested
`AGENTS.md` files intact unless the user explicitly includes them in scope.

## Discover before changing

Read the root `AGENTS.md`, applicable nested `AGENTS.md` files, and the
repository's instruction/source-of-truth documentation. Inventory each rule
with its source, intended scope, and whether it is actionable and current.
Treat higher-authority project instructions as authoritative rather than as a
contradiction with a lower-level convenience note.

Identify genuine conflicts: rules that apply to the same situation but require
incompatible behavior, stale instructions that contradict current documented
workflow, and duplicated rules whose wording changes the decision. Present
each conflict with both sources, its practical consequence, and a recommended
resolution. Ask the user which rule to keep before moving, deleting, or
rewriting either rule. Do not silently choose between competing policies.

## Design the instruction tree

Keep the root `AGENTS.md` limited to information needed on nearly every task:

- a one-sentence repository description;
- its non-default package manager and non-obvious build, typecheck, or test
  entry points; and
- durable scope, safety, or navigation rules that genuinely apply everywhere.

Use the repository's established instructions location. For a new Sociuu-style
layout, use `.agents/instructions/`; do not create a competing `docs/`,
`documentation/`, `specs/`, or `openspec/` root merely to hold agent rules.
If project documentation already owns a documented hierarchy, link to that
hierarchy instead. Keep module-specific guidance beside the module or in a
nested `AGENTS.md` when it should not affect other packages.

Group the remaining rules by decision area, not by arbitrary file size. Common
groups include workflow and safety, architecture, data/API contracts, testing
and verification, security, and documentation. Create only groups that have
real, distinct guidance. Each instruction file should say when it applies and
link to deeper canonical documents rather than duplicating them.

## Propose, then apply

Before editing, show the user:

1. unresolved contradictions and the choice needed for each;
2. the minimal root content and proposed instruction tree;
3. a mapping from every retained rule to its new owner; and
4. deletion candidates, labeled **redundant**, **vague**, **obvious**, or
   **stale**, with a concrete reason.

After conflicts are resolved, write the minimal root file, the scoped
instruction files, and only the necessary documentation indexes. Use relative
Markdown links. Preserve the meaning, authority, and discoverability of
retained rules; do not duplicate a rule across root and child files merely for
convenience.

Do not delete source instructions, historical records, or an existing
instruction tree without explicit authorization. When removal is authorized,
prefer a tracked deletion-candidates record when the repository already uses
one; otherwise report the candidates in the handoff.

## Verify

Read the resulting instruction chain as an agent would: root first, then the
files relevant to one representative task from each affected area. Confirm
that links resolve, every retained rule has one clear owner, nested guidance is
reachable, and the root contains no task-specific or language-specific noise.
Run the repository's documentation or catalog validation when available.
