# Kit source publication readiness

Kit #11/#13; coordinated with Engineering Kit #8. Audited accepted main:
`437040274f37ebe1baff289d6f75e4addea5c287`. Candidate full HEAD, tests and exact-head CI live in the Draft PR
handoff so this document does not claim its own commit hash.

## Decision and actual status

The owner selected **MIT** for both repositories and authorized changing the
**existing** canonical repositories to public after safety/rights checks and
independent ChatGPT technical review/approved merges. These decisions are settled;
no second license or visibility decision is required. No third repository,
release infrastructure, tag or GitHub Release is needed for source publication.

At preparation both repositories are **PRIVATE**. MIT and documentation changes
are proposed in separate Draft PRs. No independent ChatGPT ACCEPT or formal
GitHub approval has been obtained by the author. Publication is **BLOCKED by
unreviewed/unmerged changes**, not by a missing owner license/visibility choice.
Keep Draft until independent acceptance. Do not treat author checks as review.

## Incremental exposure and rights assessment

Reuse the [previous whole-history audit](https://github.com/AlexandrShapkin/codex-engineering-kit/blob/61a5fde6d146b83add3eaedda2a7d959f924e340/docs/PUBLIC_READINESS.md)
and its source/object hashes; [current machine inventory](PUBLICATION_AUDIT.json)
binds fresh canonical mirrors, all advertised branches/PR refs and newly reachable
objects. No prior evidence is deleted. The new scan covers source, embedded
bundles, commit metadata and deleted paths through the baseline plus delta.
A supplemental check covers all available Issues/PRs, comments, reviews, Releases,
Actions logs/artifacts and other enabled repository exposure surfaces.

| Finding | Classification | Decision/remedy |
| --- | --- | --- |
| Owner-controlled code/docs and exact imported workflow snapshots | SAFE TO PUBLISH under the selected MIT grant | Root LICENSE and [source-rights record](SOURCE_RIGHTS.md); retain copyright/permission notices |
| Credentials, private keys, genuine private-host data, proprietary binaries/assets | No confirmed finding in audited scope | Stop only affected publication if a new confirmed finding appears; never copy values into reports |
| New task-local evidence paths, historical author metadata, product names, internal links and full SHA pins | SAFE TO PUBLISH as useful provenance | Preserve; names/references grant no third-party rights and need no history rewrite |
| Prior no-license/private-source assumptions | REQUIRES REMEDIATION, prepared in this Draft | MIT plus current source/transport documentation; independent review/merge pending |
| Historical private bundles/locks | SAFE as source compatibility/provenance, not approved public transport | Preserve exact bytes/pins/classifiers except the explicitly reviewed Template admin source update |
| Public bundle approval / release qualification | Separate, not established by source visibility | Format 3 retains exact-byte approval/digest gates; format 1/2 remains private |

The available GitHub logs had no credential-shaped finding. No retained Action
artifacts, deployment records, environments, caches, Release assets or attachment
links were found; wiki/Pages/discussions are disabled. A dedicated scanner is not
installed (gitleaks/trufflehog/detect-secrets/trivy/git-secrets/semgrep absent);
no dependency was installed. Reused bounded redacting scans and manual source/
provenance review are evidence, not a proof that undisclosed/unreachable server
objects or deleted/expired material are clean. No actionable history exposure was
identified that warrants rewriting, remote-ref deletion or GitHub cache removal.
Original author metadata is retained, with no personal email values duplicated.

## Compatibility, source use and rollback

The Kit administrative lock remains at canonical source
`89cecbb4f44506f79ad3c5a22cb713429adea8a5`; legacy technical files and all
source/bundle pins are unchanged. Its retained OWNERSHIP wording is a historical
private-transport snapshot; this owner decision applies to source visibility.
Kit does not fork Template's lifecycle or silently consume its unreviewed new pin.

Trusted full-SHA source checkouts include usable Python tooling (Kit) or template
scaffolding/checks (Template), documentation and LICENSE; no redundant package is
required for reading/using public source. Significant distributable Releases and
assets remain separately qualified under Kit #13. Never upload a private bundle,
convert a private manifest, extend either six-path set, auto-update consumers or
infer publication authority from a source checksum. A public consumer migration
must preserve MIT notices outside the managed sets and verify its native gates.

Rollback before merge: leave main unchanged and close/abandon the Draft only by
owner decision; preserve its branch/evidence while active. After an authorized
merge, use a reviewed revert plus full native checks/CI, never rewritten history.
Reverting a license does not revoke rights already granted or undo public
exposure. If a genuine historical secret emerges, stop, arrange owner-controlled
revocation, enumerate all affected refs/PR refs/caches/pins/consumers and obtain
separate authority for any remote history remedy; changing main alone is not erasure.

## Completion sequence and remaining work

1. Independently review the complete Draft diffs, source rights, preserved pins,
   negative tests and exact-head Python 3.11–3.13 CI. Author verification is separate.
2. After independent acceptance and an approved merge, verify accepted merge SHA,
   rerun full checks/CI and refresh only newly exposed refs/comments/logs/artifacts.
3. Execute the existing owner visibility authorization for each repository when
   its safety checks pass. Do not request the same decision again. Verify actual
   GitHub `private=false` and anonymous repository/source access; report PUBLIC
   only from those observations, not from this prepared document.
4. Then update Kit #8 and resume the RustCraft pilot and sequential consumer Draft
   PRs, preserving active stacks, native gates and runtime boundaries. Source
   publication does not claim consumer integration or public-bundle acceptance.

The known real CLI instruction-read probe remains environment-blocked and is a
separate rollout verification item; do not repeat it in this unchanged environment.
It does not block an otherwise reviewed source-only visibility change.

Debt: owner AlexandrShapkin; P1 independent publication acceptance/merge under
Kit #11/#13, then Kit #8 public-format/collision/native-gate rollout. No new service,
orchestrator, dependency, background cleanup or weakened security gate. New task
branches/checkouts/mirrors and audit logs are retained as active review evidence;
existing branches/worktrees/dirty data remain untouched. No destructive cleanup,
remote deletion or measured-space-reclaimed claim.
