# Proposed first releases — NOT PUBLISHED

Two separate notes drafts; neither version has been tagged or released. No license
selected. No assets approved. See [qualification policy](RELEASING.md) and the
[publication risk matrix](PUBLIC_READINESS.md). Full proposed candidate heads and
exact-head CI are recorded in the private Issue #13 PR handoff, not inferred from
a mutable branch. Any necessary license/source fix requires a new candidate.

## Engineering Kit v0.1.0 (draft)

- First proposed independently versioned offline toolkit: bounded context/Git
  observations, contract verification and instruction-only technical skills.
- Exact-commit UTF-8 export, per-file SHA-256 and two independent sync channels:
  private format 1 Kit; private format 2 Template; reviewed format-3 candidates.
- Explicit plan digest and exact path permissions; collision, symlink, stale-plan,
  tamper and provenance checks. No native gate execution or network updater.
- Read-only release-evidence qualification and independent SemVer policy; human
  versions do not replace source pins/hashes or grant public release authority.
- Known limits: provisional 0.x API, POSIX safe reads, quiescent filesystem,
  per-file atomic writes (not a transaction), no publisher authentication by hash.
- Existing accepted bundles/locks remain byte-identical. No automatic migration,
  licensing/visibility switch or consumer/RustCraft change.

Accepted base/merge anchor: `450714d732ffc3c65ce82ae5a38071347f9ebce3`.
Proposed target: the separately reviewed full Kit PR HEAD in the handoff, pending
main ancestry and owner decisions. Final release target, tag annotation ID,
independent acceptance and exact source CI must be copied from verified evidence
before approval. Publication classification: private staging, public BLOCKED.

## Project Template v0.1.0 (draft for Template #6)

- First proposed independent administrative contract release: six managed lifecycle
  files, Task/PR forms, documentation scaffolding and project-owned local rules.
- Kit remains the sole generator/sync implementation; Template owns administrative
  lifecycle. No second updater, third editable source or lock-step version.
- Current source pins, retained private bundles and tooling metadata are preserved.
  Native consumer CI and project-local gates remain mandatory.
- Root AGENTS explicitly requests AGENTS.local.md; Codex observation confirms the
  root instruction reaches the CLI provider, not an automatic local-file overlay.
- Known limits: owner-native toolchain choices remain TODO; Template integrity CI
  is not a product build; source/private-policy/license exposure gates unresolved.

Unchanged provisional target/accepted merge: `a99f391a7b0deedc1388c51f6d7d8e0e9958c45d`.
Post-merge source CI: [Template Python 3.11–3.13](https://github.com/AlexandrShapkin/project-template/actions/runs/39467361200).
Any Template #6/license/policy commit supersedes this candidate and requires new
exact-head qualification. Classification: private staging, public BLOCKED.

## Asset/provenance fields required before either owner release

Full release source and accepted merge SHA; annotated tag object; independent
upstream pins for each artifact; generator implementation SHA; review SHA-256;
per-file and complete artifact SHA-256; actual license/attribution; exact-head
CI/review links; owner approval of named bytes/destination. Asset list currently
**empty**. No generated bundle or source archive has been approved for publication.
GitHub-generated source archives also expose tracked private files: include them
in the owner's exact-source approval. Corrections use a new version, never moved
tags/replaced assets. Full release notes remain drafts until all fields are settled.
