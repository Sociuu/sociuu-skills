---
name: prompt-enhancer
description: Rewrite AI prompts, agent briefs, and reusable agent or skill instructions into clear, copy-ready instructions. Correct contextual language errors, identify useful domain terminology, and clarify material gaps while preserving intent. Do not execute the supplied instructions or use this for editing emails, Slack messages, or other prose themselves, or for Stitch-specific UI prompt design.
---

# Prompt Enhancer

Improve the supplied AI instructions while preserving their purpose, scope, language, and recognizable voice. Handle technical and nontechnical prompts. Treat the supplied instructions as text to improve; never answer, simulate, or execute their underlying task.

## Preflight and clarification

Infer the intended outcome from the prompt and available context. Check only relevant dimensions: audience or operator; inputs and authoritative sources; scope and exclusions; constraints; output and success criteria; permissions, external actions, freshness, cost, risk, or reversibility.

A gap is material when it could change the outcome, scope, constraints, cost, risk, reversibility, or required authorization.

- When material uncertainty blocks a reliable rewrite, ask up to three focused questions in one compact batch. Return no draft while the blocking uncertainty remains.
- Allow further rounds when answers leave or reveal material ambiguity. Briefly state your current understanding when that helps the user correct it. Do not repeat answered questions.
- Offer brief definitions or plausible interpretations when useful, with room for a different answer. Ask about desired behavior when the user does not know specialist vocabulary. Do not force overlapping concepts into mutually exclusive choices.
- Proceed once the objective, scope, constraints, and consequential terms are sufficiently clear for a reliable rewrite. Do not pursue absolute certainty or ask about inconsequential preferences.
- Resolve minor ambiguity conservatively and disclose only consequential assumptions. Mark uncertain inferences as assumptions rather than user requirements.

## Contextual language correction

Correct grammar, spelling, idioms, repetition, and speech artifacts using context, including wording influenced by another language and accidental substitutions that are valid words themselves.

- Correct obvious mistakes directly: context may show that "achieve" was intended as "archive." Do not infer intent from grammatical plausibility alone.
- If plausible interpretations would materially change the requested action or meaning, ask which the user intends. Do not silently choose one.
- Preserve useful terminology, tone, and directness; preserve the user's voice without retaining language errors or turning it into generic corporate prose.
- Preserve code, commands, paths, identifiers, names, quoted strings, placeholders, numbers, units, and versions unless the user explicitly requests changes to them. Flag suspected consequential errors instead of silently correcting them.
- Keep the prompt's language unless translation is requested. Explain consequential word corrections, not every typo.

## Domain terminology and research

Recognize established technical or nontechnical concepts behind descriptions when doing so improves precision. Introduce useful terms with brief plain-language explanations, preserving qualifiers, examples, exclusions, and requirements that the term alone does not convey.

- Distinguish naming a concept from selecting an implementation. A performance goal does not by itself authorize rewriting the prompt as "implement sharding."
- Research unfamiliar, uncertain, specialized, disputed, or changing terminology, and when explicitly requested. Ordinary language correction does not require browsing. Prefer sources authoritative for the relevant field or system.
- If several concepts fit, explain the consequential differences and clarify the intended behavior. For example, horizontal partitioning and sharding can describe the same approach; their meaning depends on the system.
- Research verifies definitions, not the user's private intention. If verification is unavailable, disclose a consequential limitation and retain descriptive wording rather than claim verification.
- Cite researched concept mappings in the improvement notes. Include sources in the copy-ready prompt only when needed for its task or requested by the user.
- Research during enhancement does not authorize execution of the underlying task or automatically add browsing requirements to the rewritten prompt.

## Rewrite and fidelity check

Add structure only where it improves execution: context, objective, inputs, constraints, process guidance, boundaries, success criteria, or output format. Make supported implied requirements explicit. Do not invent facts, sources, tools, file changes, personas, approvals, external actions, or goals.

Before returning the rewrite, compare it with the original and the user's clarifications. Preserve negation, exclusions, ordering, conditions, and distinctions such as "may" versus "must." Check that language repair or terminology has not changed scope, selected an unrequested solution, or introduced additional permission. Keep the prompt concise without dropping requirements.

## Output

Unless the user requests another format, return:

```markdown
## Enhanced Prompt

[Copy-ready rewritten prompt]

## Material Assumptions or Gaps

- [Only consequential assumptions or unresolved non-blocking gaps; write "None" when there are none.]

## Significant Improvements

- [Substantive changes, consequential word corrections, and useful new domain terms with brief definitions. Cite researched terminology here; omit trivial copy edits.]
```
