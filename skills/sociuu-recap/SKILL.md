---
name: sociuu-recap
description: Give a concise, numbered recap of the latest work or an entire Sociuu task when the user asks what happened or what a task is about. Use Sociuu Explain to drill into one item.
---

# Sociuu Recap

Give the reader a fast, trustworthy map. Keep only the details that help them
choose whether and where to look closer. Do not explain every item in depth.

## Choose the source

Use **latest-work recap** when the user asks what just happened, what was done,
or for a summary of the last response/work process. Summarize the latest
relevant completed work, not the whole task history.

Use **task recap** when the user asks what a thread/task is about, needs to
enter an unfamiliar task, or asks for a handoff-style orientation. Read enough
available history to identify the original ask, material scope changes, and the
current state. When summarizing a different task, use its available task or
conversation history rather than its title alone. If the accessible history is
incomplete, say so plainly.

## Output

Start with a one-sentence bottom line. Follow it with a flat numbered list of
three to six short, decision-relevant items. Keep each item to one or two
sentences, so the reader can reply with `expand 3` or `explain 3`. Numbering is
local to the recap; do not claim it remains stable after a new recap.

For a latest-work recap, include only the applicable items:

1. Outcome, finding, or change
2. Why it matters
3. Decision made or proposed
4. Open work, risk, or blocker
5. Next action

For a task recap, include only the applicable items:

1. Original ask
2. Current problem and goal
3. Chosen or proposed approach
4. Important decisions, scope changes, or deliberate exclusions
5. Current state
6. Next action or decision needed

Label proposals, settled decisions, completed work, and unknowns accurately.
Do not present discussion as a decision, nor a plan as completed work. Mention
an exclusion only when it prevents a likely misunderstanding. If nothing is
open, say that rather than inventing a next step.

This skill compresses and orients. When the reader wants to understand a
numbered item, use Sociuu Explain on that item instead of expanding every item
in the recap.
