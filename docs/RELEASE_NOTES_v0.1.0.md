# Engineering Kit v0.1.0 — release candidate, unpublished

Kit gives maintainers a way to review shared engineering references before
adopting them. This first proposed version names the existing offline export,
validation and update workflow while retaining full source SHAs and content
hashes as the machine identities. It does not update consumers automatically.

- Review deterministic path/hash plans before writing. Drift, unsafe paths,
  symlinks and stale permissions stop an update rather than replace local work.
- Update technical references independently of Template's administrative policy.
  The source-update adapter supports the four already accepted consumer source
  records; it does not manufacture bundle locks or artifact approvals.
- Keep native project checks, product/security rules and independent review.
  Read-only observations do not execute product verification or grant authority.

The proposed deliverable is the minimal six-file format-3 reference bundle,
SHA-256 sums, full provenance and MIT notice described in [qualification](RELEASING.md).
Other profiles and a CLI installer are not qualified for this first matrix.
Source is PUBLIC/MIT; no tag, Release or generated artifact is published here.
Exact candidate SHA, CI/review URLs and final named asset hashes belong in the
PR/Issue handoff; these notes are finalized only after that evidence is accepted.

Compatibility is provisional `>=0.1.0,<0.2.0` for compatible patches. Python 3.11+
and POSIX are required for safe sync; use a quiescent checkout. Writes are atomic
per file, not across the whole update. Hashes do not authenticate a publisher.
Existing private formats remain private and consumer pins remain independent.

Adoption needs a separate reviewed consumer PR with all native checks and an
independently approved artifact digest where applicable. Retain the previous
source snapshot/record and use the affected channel's reviewed revert or older
revision plan for rollback. Never move a published tag or overwrite a release
asset; correct a published release with a separately approved patch.
