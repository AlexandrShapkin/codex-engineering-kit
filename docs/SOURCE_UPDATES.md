# Reviewed source proposals — Kit #8

Kit owns the only update engine; Template owns administrative policy. The four
accepted consumer migrations use `reviewed-public-source-migration` source.json
records, **not** bundle locks. `source-update` is a compatibility adapter over the
same drift checks, filesystem validation, plan digest, exact path preflight and
per-file writer as sync. It never manufactures a bundle lock or publishes an
artifact. Existing formats 1/2/3 and their authorization rules are unchanged.

## Trust and detection

Use independent trusted canonical checkouts. Authenticate their origin and full
commit SHAs through the owner/review channel before executing Kit code. The
source path alone, remote name, MIT license or SHA-256 does not authenticate an
owner or prove approval. Select accepted full source SHAs separately for Kit and
Template; verify their CI, source diff, license/rights, notices and local policy
compatibility. Public MIT source does not approve distribution artifacts.

Fetch upstreams deliberately with ordinary Git outside this offline command.
Compare the recorded revision to the selected immutable upstream commit using
`git log OLD..NEW` and `git diff OLD NEW -- SOURCE_PATHS`. A same-byte revision
advance is provenance-only; inspect it rather than claiming a policy change.
No polling service, write-token workflow, dependency installation or orchestrator
is added. A bounded operator run against each consumer detects differences;
unchanged plans need no PR. Keep two independent source checkouts and revisions.

The fixed maps are the existing six administrative paths and the six minimal
Kit paths in sync.py. No source path, profile or local rule can expand them.
The record's original `license_at` remains unchanged. A different LICENSE blocks
updates for separate rights review. Historical source commits lacking LICENSE
are allowed only when all six payloads equal the separately recorded licensing
snapshot. This check is consistency evidence; the operator must still verify
that the actual rights decision covers those source bytes and destination.

## Plan, propose and review

Start with a clean bounded branch from freshly verified consumer main. Record
its pre-write full SHA/status and retain a recoverable Git snapshot. Preserve
unrelated branches, worktrees and pending functional PRs. Use a quiescent POSIX
checkout, Python 3.11+ and Git; unsupported hosts fail closed.

```sh
python3 -B /trusted/kit/scripts/ek.py source-update plan --channel admin \
  --source /trusted/project-template --revision FULL_TEMPLATE_SHA --root /consumer
# Review changed paths and before/after hashes, then provide EVERY exact path:
python3 -B /trusted/kit/scripts/ek.py source-update write --channel admin \
  --source /trusted/project-template --revision FULL_TEMPLATE_SHA --root /consumer \
  --plan-sha256 REVIEWED_DIGEST --allow .project-template/source.json
# This example is complete only for a record-only update.
```

For technical updates use `--channel kit`, the separate Kit source checkout/SHA,
and every changed technical path plus `.engineering-kit/source.json`. The other
channel is preserved. Replan after any change; tokens bind root path/device/inode,
installed before hashes, desired record/content and changes. The command verifies
old source blobs against the record and installed content against those hashes.
Missing/modified files, unsupported mappings, duplicate JSON keys, unsafe paths,
symlinks in root/ancestors/source tree, mixed bundle locks or wrong permissions
fail closed. Initial unmanaged adoption is deliberately unsupported.

Review `git diff` for actual text changes; the machine plan supplies deterministic
path/action and before/after SHA-256 values. Commit the six-file changes and that
channel's record together. Records use canonical sorted JSON after writing.
Consumer integrity tests pin record hashes: explicitly review and update ONLY
the affected `RECORDS` hash in the existing governance test. This is a separate
reviewed consumer-owned edit, never an implicit permission to weaken a test,
change local-rule hashes, native CI or security assertions. Preserve the MIT
notice, AGENTS.local.md, product docs, all native CI and the other record.

Open one separate **Draft PR per affected consumer**, linked to Kit #8 and its
owning Issue, using normal commits/pushes. Include old/new full SHAs, the generator
full HEAD, diff, both record hashes, native local results/limitations, exact-head
hosted CI, independent technical review and rollback. Repeat the plan (empty)
and all applicable gates. No merge is automatic; independent technical acceptance,
formal GitHub approval and explicit owner merge authority are separate.
The engine never opens a PR, pushes, changes GitHub settings or runs native code.

## Rollback and interrupted writes

Retain both old revisions, licensing identities and a verified pre-update Git
snapshot. Plan/write the older revision for only the affected channel with fresh
exact permissions, then verify payload hashes and record semantics against the
retained snapshot. Canonical serialization can differ from historical formatting;
for byte-identical rollback use a reviewed ordinary Git revert of the update
commit, including its consumer-owned integrity-pin change. Preserve later user
changes; resolve conflicts deliberately. Run native tests and hosted CI on the
rollback Draft PR and obtain independent review/owner merge authority.

Per-file atomic replacement writes the record last; it is not a multi-file
transaction or crash-durable operation. After partial I/O failure, preserve
observations and restore only affected files **and record** from the verified
pre-write snapshot, checking for intervening user edits. Replan afterward; never
delete records/locks or reset user work to bypass conflicts. No concurrent or
hostile filesystem writer is supported. Tests inject record-write failure and
verify refusal until explicit snapshot recovery, retry and rollback.

## Reproduce verification

Run `python3 -B scripts/check_contract.py --self-check` and
`python3 -B -m unittest discover -s tests -v`. Source-update regressions create
independent disposable Git sources and exercise real content changes, channels,
idempotence, rollback, drift, collisions, unsafe mappings, symlinks, license
changes, stale/cross-root permissions, CLI refusal and interrupted recovery.
`SOURCE_UPDATE_EVIDENCE.json` records an additional disposable cycle over all four
accepted consumer snapshots. It does not claim native application execution in
those fixtures. `ACCEPTED_MAIN_EVIDENCE.json` records separate actual hosted native
post-merge checks. These records describe their full SHAs, never future heads.

Reproduce the recorded actual-source cycle with independent trusted checkouts:

```sh
python3 -B scripts/check_source_updates.py --kit /trusted/kit \
  --kit-revision cdfc2050733388402a70674d22de3f9e7e2a5a74 \
  --template /trusted/project-template \
  --template-revision 8550ec7fa8f58dc41a8af652ff912b62ebf78c22 \
  --consumer /trusted/rustcraft --consumer /trusted/assistant-hub \
  --consumer /trusted/codex-smart --consumer /trusted/relayforge \
  --output /tmp/fresh-source-cycle.json
```

The fixture copies trusted local consumers to TemporaryDirectory, excludes `.git`,
refuses symlinks, compares every remaining file hash and removes only its fixtures.
Use clean clones at the recorded consumer heads to reproduce recorded file counts;
local bytecode/build outputs can change counts and must not be confused with source.
