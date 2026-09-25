---
name: sociuu-ship-hotfix
description: Release a reviewed fix to Sociuu Production on top of the version running there, for Apex, Fuse, Prime (Houston, MyHub) or Admin. Use only on an explicit Production hotfix request; ordinary releases go through staging with sociuu-ship.
disable-model-invocation: true
---

# Sociuu Ship Hotfix

A hotfix ships one reviewed fix on top of the exact version running in
Production without releasing unreleased work from the integration branch. All
deployable Sociuu repositories share this release model; confirm job names in
each repository's `.gitlab-ci.yml` before acting.

| Ref | Deploys |
| --- | --- |
| Integration branch (`poc`; Prime `main`) | Staging, automatically |
| Tag `vX.0.0.N` | Demo automatically; Production through the manual `<APP>/PRODUCTION` job |

Prime releases two applications, `HOUSTON` and `MYHUB`; treat each as its own
release.

The explicit request authorizes the steps below for the named fix and
repositories. The release owner confirms each tag before it is pushed and runs
the Production jobs; humans merge. A failed release needs a new explicit
decision to roll back or roll forward.

## Procedure

1. **Scope.** Identify the reviewed fix (MR or commits), its ClickUp task, and
   every affected repository and application. Confirm its tests and review
   passed.
2. **Baseline.** For each application, find the tag of the last successful
   `<APP>/PRODUCTION` job and confirm it against the running version. Filter by
   job: Houston and MyHub share one `permanent/production` environment. If the
   integration branch has nothing unreleased beyond that tag, stop and use an
   ordinary release.
3. **Branch.** In a task worktree, create `hotfix/<task-key>` from that tag and
   apply only the fix. Keep conflict resolution minimal and run the
   repository's focused tests.
4. **Merge-back MR.** Open an MR from the hotfix branch to the integration
   branch, noting any original MR it replaces.
5. **Collisions.** Check that no other tag pipeline or Production deployment
   is running, and ask the release owner to tell the team before tagging.
6. **Tag.** Run `git fetch --tags` and push the next unused number from
   `git tag -l 'v*.0.0.*' --sort=-v:refname` on the hotfix branch head; tags are
   never moved or reused. Confirm the format with the release owner when a
   repository has no `vX.0.0.N` tags yet (Admin uses `v3.2.x`). For several
   repositories, release providers before consumers (Apex before Fuse and
   Prime) unless the change requires another order.
7. **Demo.** Wait for the Demo deployment and verify the fix and adjacent
   behaviour on Demo. If Demo fails, stop before Production and report.
8. **Production.** The release owner runs `<APP>/PRODUCTION`. Verify the
   deployed tag, the fix and error monitoring before releasing the next
   application.
9. **Finish.** Ask the release owner to close the team notice. After the
   merge-back MR is merged, close any superseded original MR, post a
   release-note comment on the ClickUp task (tags, applications, user impact)
   and set it to `complete`.

Report the exact tags, deployments, verification results, open MRs and any
human action still required. A tag or a green pipeline alone is not a
Production release.
