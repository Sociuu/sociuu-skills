---
name: sociuu-cleanup
description: Clean up and close out Sociuu work — worktrees, Dock environments, branches, MRs, ClickUp status, follow-ups, disk. Use whenever the user says cleanup, clean up, tidy up, housekeeping, "anything left", "anything hanging", "are we done", "is this thread done", "can I archive this", or asks what is left after a merge. Also use unprompted once a task's MRs are merged.
---

# Sociuu Cleanup

Two modes. With a task, run that task's post-merge close-out list. Without one,
sweep everything below.

Read first, then act only on what the user confirms in this session. Another
task's worktree, Dock environment or MR is reported, never touched.

## Sweep

Build one table of findings from the workspace isolation inventory, the Dock
environment list, the forge's open merge requests for the current user, and the
task tracker's unfinished tasks. The inventory can take minutes; run it in the
background and read each worktree's status, cleanliness, branch and age
together. Age alone decides nothing.

For each finding, state what it is, which task owns it, and one of:

| Verdict | Meaning |
| --- | --- |
| Safe to remove | merged and clean; propose the exact command |
| Keep | another task owns it, or it is dirty, unpushed or in use |
| Needs a decision | the task looks finished but the record or branch disagrees |

## What to look for

1. **Worktrees** whose branch is merged or gone, and empty task folders left
   behind. Release through the isolation provider's cleanup, never `rm`.
2. **Dock environments** with no task, or whose task is merged. Stop and remove
   only those; report the rest with their owning task.
3. **Branches and MRs**: merged branches still present, MRs open on merged work,
   MRs with unresolved review threads, drafts nobody is finishing.
4. **Task records**: merged work not in `done`, released work not in `complete`,
   tasks with no MR link, and discussed-but-never-created follow-ups.
5. **Disk**, when Dock is short: reclaim inside the Docker VM first, then remove
   environments one by one. Never a broad Docker prune.

## Retention rules

Keep a worktree that is dirty, unpushed, shared, or still the working directory
of a running process — including a tunnel or a test run started from it. Report
why rather than forcing it. A worktree behind an open MR is kept by default; the
branch is preserved either way, so removal is safe once the MR merges.

Releasing a worktree records its final revision, so the work can be restored.
Removing a Dock environment does not: capture any evidence that lives only in
that environment before it goes.

## Report

Lead with the count of items needing action and the one command to start with.
Group by verdict, newest task first. Finish with what was cleaned, what was left
and why, and any follow-up task created.
