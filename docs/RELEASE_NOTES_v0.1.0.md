# Proposed v0.1.0 release notes — unpublished drafts

Neither project has released v0.1.0. Public delivery remains blocked by license,
rights, disclosure review and separate owner approval. The shared release-writing
and artifact rule belongs to [Template #6](https://github.com/AlexandrShapkin/project-template/issues/6);
these are the two concrete drafts for that review, not another universal policy.

## Engineering Kit v0.1.0

Kit already supports reviewed offline updates, but operators have no published
version or qualified release package to choose. This proposed first release would
make that existing workflow easier to identify and assess: a named toolkit with
reviewable profile bundles and a read-only check of release evidence. It would
not install itself or update any consumer automatically.

- **See the update before accepting it.** Operators can inspect a plan and grant
  permission for its exact changed paths. Existing-file conflicts stop the update;
  local instructions and native CI remain under the consumer's control.
- **Choose a version without losing its source.** The release name helps people
  select a candidate, while the reviewed commit and content hashes still identify
  the bytes. Technical and administrative updates can advance or roll back
  independently rather than forcing a combined upgrade.

Existing accepted bundles, locks and pins remain unchanged; adopting a version
still needs a separately reviewed consumer PR. The 0.x interface is provisional.
Safe sync requires Python 3.11+ on POSIX and a quiescent checkout; writes are atomic
per file, not a multi-file transaction. Hashes do not authenticate a publisher.
The [planned assets](RELEASING.md#planned-v010-assets) are not available or approved.
For implementation detail, see [Kit #12](https://github.com/AlexandrShapkin/codex-engineering-kit/pull/12)
and [this qualification PR](https://github.com/AlexandrShapkin/codex-engineering-kit/pull/14).

## Project Template v0.1.0

Template already separates common workflow from project-specific rules, but has
no published administrative release to select. Its proposed first version would
give maintainers a reviewed administrative bundle with a clear source, without
making every project hand-maintain its own version of the shared lifecycle.

- **Keep project decisions local.** Common workflow updates use the Kit sync
  mechanism; native commands, CI and product rules remain consumer-owned.
  An existing AGENTS.md causes a collision and needs an explicit migration,
  rather than being replaced during adoption.
- **Update administration on its own schedule.** A Template release does not
  re-pin the installed Kit or force another channel's upgrade. Maintainers can
  review and roll back each channel independently using retained bundles.

Current private bundles, locks and tooling pins are preserved. The 0.x contract
is provisional, and integrity CI is not a product build. Root AGENTS.md explicitly
requests reading AGENTS.local.md; real-model compliance and automatic inclusion
are not established by the recorded CLI observation. No rollout to existing
consumers or public distribution is claimed. See the [planned administrative asset](RELEASING.md#planned-v010-assets)
and [Template #5](https://github.com/AlexandrShapkin/project-template/pull/5).

## Candidate evidence and availability

Kit's accepted base is `450714d732ffc3c65ce82ae5a38071347f9ebce3`; its revised
full candidate HEAD and exact-head CI are recorded in the private PR #14 handoff.
Template's unchanged provisional target is `a99f391a7b0deedc1388c51f6d7d8e0e9958c45d`
([accepted-source CI](https://github.com/AlexandrShapkin/project-template/actions/runs/39467361200)).
Neither is an owner-approved release target. License or source fixes require new
candidates and verification. No assets were generated for this plan; final names,
source/annotation IDs, approved hashes and license notices remain unresolved.
