# Public-safe distribution proposal — Issue #11

Private staging only. No license, release, public repository, visibility change,
consumer modification or publication is authorized. PUBLIC-SAFE describes reviewed
content; it is neither permission nor authentication. The private format-1/2
protocols and the default CLI behavior remain unchanged.

## Sources and release form

Kit owns technical source, packaging and the only sync engine. Template owns
administrative source and lifecycle. Use two immutable JSON artifacts, one per
channel/profile, generated at independently reviewed full upstream commit SHAs.
Prefer a separately owner-authorized release-only distribution repository with
immutable artifacts and checksums, over repeating transport of private sources
in every consumer. It would contain generated output only, no editable policy,
private Git history, checkout, bundled interpreter or background updater. This
repository/destination does not exist and creating it requires explicit approval.
Manual transfer of the same approved artifact is also possible; each consumer
still gets a separate Draft PR with mandatory native/platform/security checks.
Neither channel upgrades, publishes or rolls back the other.

Generation reuses export: exact regular Git blobs, UTF-8, deterministic sorted
JSON, no timestamps, network, transformations, tool installation or working-tree
content. No redaction is performed during packaging. Source refactors belong in
the owning canonical repository with independent version/review. Frozen Kit v0.1
contracts are unchanged. Introducing a safe replacement requires a separately
reviewed source/protocol decision, never a hidden third copy of admin policy.

## Audit and release blockers

[The exact inventory](PUBLIC_DISTRIBUTION_AUDIT.json) contains six Kit and six
Template destinations, original source paths, all full SHA-256 values, byte sizes,
markdown links, skill frontmatter, content classification and release restrictions.
It is private evidence, not a release review input. Reproduce it with local Git
objects (template-source must contain the pinned Template commit):

```sh
python3 -B scripts/audit_distribution.py --kit-source . \
  --template-source /trusted/template --output docs/PUBLIC_DISTRIBUTION_AUDIT.json --check
```

Pins: Kit baseline e647d9d535eb9b55f2a6df55c2bf5e4b9a47957d;
admin implementation 21cf2914cb0a1c904ca8c783a36723786373b600;
Template source 0a53f56dba841675b3203a76e33594fee1a73b9f.
The generator implementation is the separately reviewed PR HEAD, not the baseline.
Only minimal profile was audited; other profiles require their own reviewed bytes.

Six files have PUBLIC-SAFE content classification; six need REDACT/REFACTOR
review (see inventory). All twelve are BLOCKED for actual publication pending
license/rights and explicit named-byte approval. Historical private Issue URLs,
product names, owner names, full private commit IDs, frozen policy duplication,
relocated links and consumer-owned prerequisites require review. OWNERSHIP.md's
private-only statement is not overridden by a transport label. No credential,
secret, proprietary binary/asset or private host address was found in these twelve
text blobs by content review; this does not clear their history, other files,
other profiles or repository contents. No private checkout/history is packaged.
Missing consumer docs are prerequisites, never implicitly added to the allowlist.

## Candidate protocol and explicit boundary

Format 3 is an envelope with exactly format, publication=public-safe, channel,
canonical owner, generator (full Kit implementation SHA), review (SHA-256 of
external review bytes), and source (the original private format-1/2 manifest).
The unchanged nested manifest is provenance, not a permission conversion.
Full source/file hashes and exact six-file sets are validated per channel.
The consumer lock stores this envelope, with separate existing lock paths.
Public/private lock transitions fail closed; migration needs separate review.

Prepare an external review JSON only after actual source review. Its exact schema
is format=1, channel, upstream (full source SHA), files mapping **all six**
destinations to objects with sha256 and classification="PUBLIC-SAFE".
Extra/missing files, different hashes or unresolved classifications fail generation.
A review author must not turn inventory findings into PUBLIC-SAFE by bulk relabeling.
The review digest pins classification, not identity, license or owner permission.

From a trusted checkout of the separately reviewed full Kit generator SHA:

```sh
python3 -B scripts/ek.py distribution --channel kit --source /trusted/kit \
  --revision FULL_KIT_SOURCE_SHA --profile minimal --review /private/review.json \
  --review-sha256 REVIEW_SHA256 --generator-revision FULL_GENERATOR_SHA \
  --output /private/candidate.json
# admin uses --channel admin --profile administrative --source /trusted/template
```

Verify the generator checkout/code against FULL_GENERATOR_SHA independently;
this field is supplied provenance, not a signature/attestation. Generate twice to
fresh paths, compare exact bytes and SHA-256, then independently compare source
hashes, review input, links, metadata and output. Existing output paths are refused.
The command returns publication_authorized=false. No candidate of the audited
baseline is eligible while its inventory contains unresolved findings.

Only after the owner separately approves the **named artifact bytes/digest**,
license and exact destination, an operator may transfer those bytes. On adoption:

```sh
python3 -B scripts/ek.py sync plan --channel kit --root /disposable/consumer \
  --bundle /trusted/approved.json --public-bundle-sha256 OWNER_APPROVED_SHA256
# Review changes and token; write uses the same flag and one --allow per changed path:
python3 -B scripts/ek.py sync write --channel kit --root /disposable/consumer \
  --bundle /trusted/approved.json --public-bundle-sha256 OWNER_APPROVED_SHA256 \
  --plan-sha256 PLAN_SHA256 --allow EXACT_CHANGED_PATH
```

The example write is incomplete unless only that path changes. The explicit
public digest rejects private bundles even when their digest matches. Format 3
without that flag is rejected. Recomputing a digest after changing metadata is
not owner approval. The offline tool cannot verify a human's authority or remote
visibility; approval must arrive independently of the artifact via a trusted owner
channel. Never derive the approved value automatically from an untrusted download.
This is a bounded operator workflow, not a signature trust infrastructure.

## Threat and review matrix

| Threat | Enforcement / remaining gate |
| --- | --- |
| Private bundle relabeled public | Formats 1/2 unchanged; format 3 separate validation and explicit external artifact digest |
| Content/classification tamper | Review pins all six source hashes; transport SHA-256 pins entire envelope; source hashes checked again on read |
| Forged author/owner/approval | Owner/channel allowlist checks structure only; independently trusted human authorization required, hashes do not authenticate |
| Source or generator version drift | Full separate SHAs, committed source blobs, repeatability; reviewer must verify generator checkout and exact-head acceptance |
| Unexpected paths, overlap, symlinks | Exact channel public set plus existing path/read/preflight validation |
| Stale/overbroad permissions | Existing root/device/inode/before-state token and exact path set reused |
| Native rules/CI overwritten | CI/local/stage/architecture paths excluded; unmanaged AGENTS/interface hard collision; explicit reviewed migration required |
| Partial write/concurrent writer | Existing per-file atomic replacement, lock last; quiescent checkout and verified snapshot recovery, no multi-file transaction |
| Missing linked documents/license | Publication review blocker; no implicit link fetch, file expansion or licensing decision |

## RustCraft and acceptance evidence

Automated tests use synthetic reviewed sources for both channels and a disposable
public-like RustCraft fixture: AGENTS/interface collisions, native CI/gates and
architecture/stage byte preservation, independent update/rollback, stale plans,
path/manifest/symlink conflicts, wrong permissions, altered review/classification,
private-bundle rejection, deterministic export and no sync network/processes.
A separate local evidence report exercises copied actual RustCraft native files;
no RustCraft writes, remote consumer branches or PR #36 updates are permitted.
Fixture preservation does not prove Rust compilation: full just ci, Ubuntu and
Windows exact-head migration CI remain UNVERIFIED until a separately authorized
consumer migration. Kit Python CI does not substitute for them.

Keep both private PRs Draft until independent technical review. CI author checks,
formal approval, owner merge, license choice, publication of each named artifact,
public distribution destination creation and later RustCraft migration are separate
gates. Issue #11 remains open while those acceptance/publication decisions remain.

Reproduce the read-only real-file fixture (requires the three pinned source
commits present locally in the Kit Git object database):

```sh
python3 -B scripts/check_public_fixture.py --rustcraft-source /trusted/rustcraft \
  --output /private/fresh-fixture-report.json
```

[Recorded fixture evidence](RUSTCRAFT_PUBLIC_FIXTURE.json) covers RustCraft HEAD
5b09106c814ac1ee59e8b8e3d2e0688180115964. At inspection PR #36 remained Draft/open
at 09e5b3ecd482db53b6919c329ab348e230572f94. Its actual root has no development
interface yet; AGENTS collision was observed. Native justfile defines the full ci
recipe. The script copies 20 committed files, uses synthetic public bytes only,
asserts preservation and removes only its own disposable fixture via tempfile.
