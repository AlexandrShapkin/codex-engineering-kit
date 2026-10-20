# Public readiness — historical audit, Issue #13

Historical snapshot below. Owner has since authorized MIT and public source
visibility after safety/rights checks. See [current publication delta](PUBLICATION.md)
for superseding decisions and actual review/visibility status. Old asset-release
restrictions and immutable source pins are not silently changed.

**Kit: BLOCKED. Template: BLOCKED.** Both remain private, no license selected,
no real tags/Releases/assets created. The accepted anchors are Kit
`450714d732ffc3c65ce82ae5a38071347f9ebce3` and Template
`a99f391a7b0deedc1388c51f6d7d8e0e9958c45d`. They are verified bases, not owner
release approvals. [SemVer/release qualification](RELEASING.md) and
[draft notes](RELEASE_NOTES_v0.1.0.md) do not authorize publication.

## Scope and evidence

[Sanitized machine inventory](PUBLIC_READINESS_AUDIT.json) records **all 35
tracked paths in each accepted tree**, regular-file modes, exact blob IDs,
SHA-256/size for each file, every advertised canonical ref and reachable object
counts. Independent mirror clones captured all heads and advertised PR refs;
`git ls-remote` was compared with mirror refs exactly. No local foreign Template
objects were included in Kit's scope. Mirrors had no tags. GitHub Releases,
including drafts, were empty; there is no established tag/release convention to
migrate and proposed `v0.1.0` is unused. Template remains `is_template=true`.

Kit: 25 reachable commits, 76 trees, **80 blob versions**. Template: 9 commits,
30 trees, **45 blob versions**. Every reachable blob and raw commit/tag metadata
was inspected by the redacting scan, including deleted Kit
`engineering_kit/github_public.py`; Template has no deleted paths. All blobs were
UTF-8 text, with no binary/proprietary assets, LFS pointer files, submodules or
symlink modes found. Object inventory hashes in the JSON bound this snapshot.
Reachability includes old branch/PR heads, not just main; it does not include
unreachable server objects, reflogs, undisclosed refs, deleted remote caches,
external linked projects or the owner's local credential stores. Those were not
read and must not be inferred cleared.

Procedure: normal authenticated canonical mirror clones; `for-each-ref`,
`rev-list --objects --all`, object-type enumeration, `cat-file` over every
blob/commit, `ls-tree -rl` at the accepted heads, and per-commit deleted-path
inventory. Rules scanned provider token/key forms, PEM private keys, credential
assignments, URL userinfo, non-fixture email, private network/local path patterns
and high-entropy strings. Matches were classified without reporting values.
High-entropy candidates were public commit signatures, GitHub provenance URLs
and the sync path validator's allowed-character alphabet. Local `/tmp` hits were
example/test output paths, not discovered private hosts. `api.github.com` is a
public service; `elsewhere` occurs in historical HTTP redirect tests.

No confirmed secret, token, private key, credential assignment, URL password or
private infrastructure address was found. This is a bounded heuristic/content
review, **not a proof of absence or an independent dedicated secret scanner**;
a separate tool/security review is UNVERIFIED (no scanner installed). No finding
currently calls for emergency rotation or mandatory history rewriting. Never
copy a newly found secret into reports; record only an affected object/location
and severity, stop publication, arrange owner-controlled revocation and review.

GitHub metadata scan covered all paginated Issues/PR bodies, issue/review comments,
reviews and Releases at the snapshot: 13 combined Issue/PR records and 18 comments
for Kit; 6 records and 5 comments for Template. No credential-pattern finding.
No inline review comments/formal review records or retained Action artifacts were
present. Wiki, Pages and Discussions are disabled. All available logs from 44 Kit and 11 Template workflow runs were pattern-scanned
with zero credential-shaped matches; byte counts are in the JSON. Inaccessible/
expired/deleted logs, if any arise later, cannot be certified clean.
Issue discussions contain historical evidence/paths and related private links;
Git object clearance does not grant permission to expose that conversation.

All original historical/current profiles, managed paths and bundles were included,
not only the twelve-file #11 audit. Kit technical profiles are minimal/backend/
infrastructure/research; product markers name the four products and stronger
native gates. Template's `.engineering-kit` baseline, private administrative
bundle/lock, ownership map and tooling source pins remain unchanged. The embedded
Kit contract snapshots are legacy provenance, not a second editable lifecycle.
The older #11 REDACT/REFACTOR findings remain release blockers, not fixed by tags.

## Risk matrix and minimum remediation

| Severity / status | Evidence without sensitive values | Minimal safe action |
| --- | --- | --- |
| P1 BLOCKED: no license | Neither tree/history has LICENSE/COPYING/NOTICE; README/local rules explicitly say no license selected | Owner chooses license/coverage/copyright holders; implement in separately reviewed exact target, regenerate only affected release bytes |
| P1 BLOCKED: redistribution rights | Kit README imports contracts from four prior product proposals; Template bundles copies of Kit; Git authorship alone does not establish rights | Owner attests rights to imported source/docs and any contributions; identify applicable upstream licenses/notices before release |
| P2 BLOCKED: personal metadata | Two distinct author/committer email identities per repository, including personal contact data; raw commits preserve them | Owner explicitly approves exposure or authorizes a separately planned metadata/history remedy; no email values reproduced here |
| P2 BLOCKED: private links/project disclosure | Kit README, contracts, profiles/products.json, provenance JSON and Template retained bundles/docs name related repos, Issues/PRs, product gates and source SHAs | Decide which historical provenance may be public; otherwise refactor current owner-controlled sources and separately review history exposure; do not silently rewrite frozen snapshots |
| P2 BLOCKED: publication-policy mismatch | Format 2/tooling and Template OWNERSHIP/UPGRADING say private; #11 inventory has unresolved source/link classifications | Keep formats unchanged. Review canonical policy exceptions in Template #6, then new source pins/classification review and named artifact approval |
| P2 BLOCKED: content outside managed sets | AGENTS/WORKFLOW reference consumer INDEX, AGENTS.local, PROJECT and UPGRADING; none implicitly extends the six-file public allowlist | Verify prerequisites in each separately authorized consumer PR; maintain native rules/CI and hard collision on existing AGENTS/interface |
| P2 UNVERIFIED: external exposure surfaces | Unreachable server objects, caches/attachments and deleted logs are outside Git mirror proof; all 55 available run logs scanned, Issues contain prior discussions | Owner/security reviews GitHub exposure immediately before visibility change; request support if historical sensitive material needs removal |
| P2 UNVERIFIED: comprehensive secret/PII clearance | All reachable bytes scanned; no confirmed credential patterns, but pattern review cannot prove absence or rights | Independent review/dedicated scanning and owner disclosure approval before public visibility; no dependency installation performed |
| P2 UNVERIFIED: enforced immutability | No release tags exist; no GitHub rules/settings changed | Treat tag/object IDs and assets as immutable by policy; verify remote observations and ask separately before configuring server enforcement |
| P3 PASS: local paths/test endpoints | Historical SYNC/UPGRADING/VERIFICATION examples; historical HTTP test implementation | Preserve as provenance if approved; do not claim they are actual deployment endpoints or secrets |
| PASS: no detected vendored/proprietary payload | 125 text blob versions, 70 current tracked paths; stdlib Python and GitHub action references, no bundled binaries/assets | Retain bounded scope; action references are dependencies, not redistributed action source; new contributions need fresh review |
| PASS: independent versions/compatibility | New policy and read-only checker add no fields to old manifests/locks and do not modify managed sources | Keep full hashes/native gates; rerun source compatibility and negative tests after any candidate change |

No published secret values, personal email addresses or raw metadata dumps are in
this report. Private evidence retains safe object/location identifiers, inventory
and scan procedures. The matrix is conservative: PASS for a test is never a
publication/license/identity grant.

## License recommendation (owner decision only)

Propose **MIT** as the minimal common license for owner-authored Kit code and
accompanying docs/skills/profiles, and Template rules/scaffolding/docs, **if rights
are confirmed**. It permits broad reuse and distribution while requiring retained
copyright/permission notices; its text expressly includes associated documentation.
It is short and suits source-only templates intended for adaptation. No license
has been applied. See the [official MIT text](https://opensource.org/license/mit).

| Consideration | MIT | Apache-2.0 |
| --- | --- | --- |
| Code and documentation | Broad grant covering software/associated documentation | Covers source including documentation/configuration |
| Attribution | Preserve copyright and permission notice in copies/substantial portions | Preserve applicable notices/license; mark modifications; carry relevant NOTICE attribution if present |
| Patents | No express patent grant in the text | Express contributor patent license and patent-litigation termination |
| Operational burden | Minimal notice handling | More notice/change tracking; useful if explicit patent terms are important |

Apache-2.0 is a reasonable alternative for an owner prioritizing express patent
terms and contribution clarity. It does not give rights to material the licensor
does not own, and neither option removes third-party restrictions or trademark
limits. Its documentation scope and obligations are described by the
[official Apache-2.0 text](https://www.apache.org/licenses/LICENSE-2.0). Preserve any
real third-party licensing; do not fabricate NOTICE or assume author identity
proves ownership. Different licenses per upstream are possible but add notice/
compatibility review for Template's retained Kit material; a shared owner-selected
license would reduce that burden. This is a technical comparison, not an owner
license selection or legal determination of third-party title.

## History remedy plan — NOT EXECUTED

No rewrite is presently justified by a confirmed secret. If disclosure consent or
rights cannot be obtained: freeze publication; inventory affected objects, refs,
tags, PRs and clones privately; obtain explicit owner decision between approving
historical disclosure, using a clean separately approved export, or rewriting
history. If a real secret appears, arrange revocation/rotation **before** cleanup.
Preserve authorized evidence/backups under owner storage rules. Prepare a mapping
of old/new commit/object IDs and provenance/consumer pin impacts; rewriting just
main does not remove old branches or GitHub PR refs/caches. Assess signatures,
future tags, Template bundles and all consumer source pins. Seek separate authority
for every rewritten/deleted remote ref and any GitHub-support request. Re-audit,
review, requalify CI and obtain explicit owner approval before any execution.
This task neither rewrites nor deletes existing refs/worktrees/evidence.

## Codex CLI observation

A real installed **codex-cli 0.162.1** process ran with an empty task-local
CODEX_HOME, no inherited credentials/user config/rules, read-only sandbox and a
synthetic loopback Responses endpoint. Its fixture used exact accepted Template
root AGENTS bytes (hash in the JSON), and an AGENTS.local.md containing a synthetic
marker. One provider request was captured; CLI exited successfully. The root
AGENTS instructions reached the provider and explicitly requested AGENTS.local.md;
the local marker was **not** automatically injected. No global configuration,
credential copy, external inference or production/consumer access occurred.

PASS: actual CLI instruction injection and explicit root directive. UNVERIFIED:
a real model following the directive and reading the local file; the fixture
provider issued no tool calls. This is not proof of an automatic AGENTS.local.md
overlay or of native gates being executed. Operators must verify actual model
reads separately before rollout. Official discovery behavior documents recognized
AGENTS files and configurable fallback names, not arbitrary automatic local
includes: [OpenAI documentation](https://learn.chatgpt.com/docs/agent-configuration/agents-md).
The observation validates the installed CLI behavior, not every future version.

## Owner gates and final state

Before either public v0.1.0: owner rights/license choice; identity/reference and
GitHub conversation/history exposure approval; any source/private-policy fixes;
new exact target and full audit delta; native exact-head CI; independent ChatGPT
review; separate merge/main ancestry; annotated tag/Release/visibility and exact
notes/assets/destination authorization. Format 3 is retained; formats 1/2 stay
private. No real tags, Releases, bundles, visibility changes or consumers are
modified here. Template #6 gets a technical plan only. RustCraft/PR #36 and full
native migration just ci/Ubuntu/Windows remain separate UNVERIFIED rollout work.
