# Kit v0.1.0 candidate qualification

Owning Issue: [#13](https://github.com/AlexandrShapkin/codex-engineering-kit/issues/13).
Template [#6](https://github.com/AlexandrShapkin/project-template/issues/6) owns
shared release policy in `.github/DEVELOPMENT_INTERFACE.md`. Kit owns technical
export, integrity and updater mechanisms. Kit #8 is CLOSED; its migrations are
complete. No new migration, runtime, tag or publication is authorized here.

## Current source and compatibility

Accepted source baseline: `8f2008dfcfa27ca1e4b4b754baecec29a22e86a0`.
Template's independent accepted baseline is
`8f964eda3f530d41f78e776a2087d0b33e570358`. Both canonical upstreams are PUBLIC/MIT;
see their accepted publication/rights records. Historical private-source and
unselected-license statements in old audits describe earlier checkpoints.
They are not new owner decisions to repeat. Fresh source/history and GitHub
surface deltas still require review before release.

The candidate containing this document is identified by the full PR head in
its handoff. A future accepted merge SHA needs its own exact-head checks; do not
predict it or treat a branch name as a pin. No `v0.1.0` tag is created by preparing
this candidate. Each repository versions independently with immutable annotated
`vMAJOR.MINOR.PATCH` tags; never move, reuse or replace a release tag.

Kit's public interface is its CLI, offline export/sync/source-update safety,
bundle/lock protocols and technical references. Compatible first-series patches
support `>=0.1.0,<0.2.0`; a breaking `0.x` change needs a MINOR increment and
migration guidance. Format integers 1/2/3 are independent wire protocols.
Full source SHAs and file/artifact SHA-256 remain authoritative. No version
implicitly advances consumer pins, installs skills or changes native gates.

## Bounded first-release matrix

| Asset | Target / use | Qualification |
| --- | --- | --- |
| `kit-v0.1.0-minimal.public-safe.json` | Python 3.11+ / POSIX; usable six-file technical reference bundle | Exact minimal-profile source-byte review and format-3 provenance; independent approved digest required before distribution/adoption. |
| `SHA256SUMS` | SHA-256 of every approved deliverable and provenance sidecar | Verify actual file bytes; checksum agreement is not publisher authentication. |
| `PROVENANCE.md` and MIT notice | Full release/source/generator/review SHAs and named asset digests; attribution | Review independently and retain MIT notice outside managed paths. |

Only the minimal profile is proposed for v0.1.0. Backend, infrastructure and
research profiles are omitted until their own exact-byte review; no empty
artifacts. A CLI installer is not claimed: the bundle supplies reference files,
not `ek` installation. GitHub automatic source archives and development caches
are not substitutes for these usable bundles. Template qualifies its separate
administrative bundle in its own repository and Release.

Private format-1/2 bundles remain compatibility/rollback evidence, never public
fallbacks. Do not manufacture a PUBLIC-SAFE review, artifact approval or sync
lock from a public license. Preparing source candidates does not clear generated
asset bytes. No upload or public artifact distribution occurs in this task.

## Qualification and exact owner action

1. Verify canonical GitHub ownership, public source/MIT, fresh accepted main,
   candidate ancestry, complete tag inventory and every Release including drafts.
   Reused names block a new release. Preserve the accepted source/history/rights
   audits; review every newly reachable delta and relevant new workflow output.
   Report inaccessible surfaces UNVERIFIED, never “no secrets” by inference.
2. Run `python3 -B scripts/check_contract.py --self-check` and the full native
   unittest suite. Require actual Python 3.11/3.12/3.13 hosted CI at the exact
   full candidate head, independent technical ACCEPT and owner acceptance.
3. Use existing export/distribution tools only with independently reviewed exact
   source-byte classification. Generate twice privately, compare bytes, verify
   every nested manifest file against canonical Git blobs and validate complete
   SHA-256/provenance/notice agreement. Retain exact named bytes for review.
4. Exercise both source channels' update/idempotence/rollback in disposable
   repositories, preserving local/native files and unrelated active evidence.
   The existing `scripts/check_source_updates.py` supports this without real
   consumer writes. Synthetic tests are not approval of actual release artifacts.
5. Finalize [narrative notes](RELEASE_NOTES_v0.1.0.md), compatibility, known limits
   and rollback. Obtain separate owner approval **for Kit v0.1.0** naming the
   exact commit, annotation, notes, canonical destination and each artifact digest.
   Template v0.1.0 needs its own distinct approval. No merge authorization is
   inferred from review/CI, and no release authority is inferred from merge.

The existing `scripts/check_release.py` is an offline consistency checker. Its
`--publication private` mode describes private staging observations even when
source is public; it always returns `publication_authorized=false` and rejects
public classification. It does not attest GitHub facts, history, licensing or
artifact safety. Do not broaden it into an authority store to get a green gate.

```sh
# Obtain a real exact-head native run; retain its actual headSha and job names.
gh run view RUN --repo AlexandrShapkin/codex-engineering-kit \
  --json headSha,status,conclusion,workflowName,jobs,url > /private/kit-ci.json
python3 -B scripts/check_release.py --source /trusted/kit --project kit \
  --version v0.1.0 --target FULL_CANDIDATE_SHA --ci-json /private/kit-ci.json
```

After separately approved publication, verify the full annotated tag-object ID,
peeled commit, notes, canonical asset URLs and downloaded hashes. A changed tag
is an incident; do not silently replace evidence. Server-enforced tag immutability
is not established by local validation; no repository settings are changed here.

## Rollback and limitations

Before adoption retain the accepted prior Git snapshot and both independent
source records. Revert a reviewed candidate change normally; for later source
updates use the retained older channel revision with a fresh exact plan and
path permissions. Preserve local rules, native CI, MIT notices and unrelated work.
Conflicts or interrupted writes require explicit snapshot recovery/replanning,
never a forced reset or deleted lock. Published assets/tags are immutable: ship
an explicitly approved new patch instead of overwriting them.

POSIX sync requires a quiescent checkout; per-file replacement is not a multi-file
transaction. Descendants escaping the dedicated process group are outside Git
observation cleanup. Hashes prove consistency, not ownership. Real Codex automatic
instruction compliance remains unproven; existing explicit local-rule reads and
native product gates remain mandatory. No release is ready until the evidence
and exact named-byte owner approvals above are complete.
