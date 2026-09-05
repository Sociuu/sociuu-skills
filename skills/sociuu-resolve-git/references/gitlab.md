# GitLab feedback adapter

Use Glab MCP when available, otherwise authenticated glab CLI.
Discover supported operations before calls. GitLab REST resources include
projects/:id/merge_requests/:iid, its discussions and commits; discussions have
reply and resolution operations. Encode project paths and paginate to completion.

1. Read MR metadata, source SHA, diff and requested discussions including replies.
2. Read the installed CE Resolve PR Feedback evaluation rubric when available.
   Use its technical judgement guidance; exclude its GitHub API/platform steps.
3. Evaluate concerns against code/spec/tests. Group the same root cause. Fix,
   fix differently, explain already-fixed/declined items, or leave a material
   unresolved decision for the human with a recommendation.
4. Make authorized fixes in the task-owned checkout, using CE Debug/Work as
   appropriate. Run affected checks, commit/push within scope and verify that
   the MR's remote source contains the fix.
5. Reply with disposition, evidence and tested revision. Search existing replies
   first to avoid duplicate posts on retries. Resolve eligible threads only
   after verifying the reply and repair; honor human questions and repository
   reviewer/bot resolution policy. Top-level comments may not be resolvable.
6. Refetch discussions and source SHA. If source changed concurrently, reconcile
   it before further mutation. Report any new or unanswered feedback.
   Do not mistake resolved-thread counts or bot rate limits for completed review.

Use structured text arguments or body files; avoid interpolation of comment
content into shell commands. Keep external-review requirements explicit.
