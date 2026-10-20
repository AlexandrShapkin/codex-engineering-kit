# Kit #15 migration evidence

Owning task: [Kit #15](https://github.com/AlexandrShapkin/codex-engineering-kit/issues/15),
coordinated with [Template #7](https://github.com/AlexandrShapkin/project-template/issues/7).
Base: `61a5fde6d146b83add3eaedda2a7d959f924e340` (accepted Kit main).
Initial checkout was clean at `b4b7e52bc1d44a7b4e4a3e8eb54dbfa8e7c46e3b`
on the merged PR #14 branch. Fetched main matched the supplied base; its CI passed
at https://github.com/AlexandrShapkin/codex-engineering-kit/actions/runs/39477011486.
A new bounded branch starts from that base. No active PR overlapped at inventory.
Final full HEAD and exact-head CI are recorded in the Draft PR handoff.

## Source and scope

The six managed administrative files are byte-identical to canonical source
`89cecbb4f44506f79ad3c5a22cb713429adea8a5` and accepted Template main
`5087295b7e571e87c3f70f721e26ff4ca7a2e315`. The retained private format-2
bundle was independently regenerated with existing export and compared byte for
byte. Its manifest is the new administrative lock; its source pin is explicit.
The taxonomy and read-only metadata checker are byte-identical manual scaffold
adoptions from accepted Template main; neither adds a managed sync path.
The self-check pins these source/export bytes and checks policy discovery,
local gates and lock/content agreement. Rehashing changed policy fails.

The only replaced existing administrative entrypoint is tracked AGENTS.md,
explicitly in this migration's scope. Its Kit-specific prohibitions and native
gates now live in AGENTS.local.md; the legacy interface activation is removed.
All other managed paths were absent. Local docs and native CI are preserved.
Legacy contract bytes, technical profiles, sync paths, private formats and existing
fixture/source pins remain unchanged. Root self-check now also verifies adoption;
legacy consumer validation retains its original semantics. No consumer is edited.

## Live GitHub inventory (2026-10-21)

All Issues #1/#3/#5/#7/#8/#9/#11/#13/#15 and PRs #2/#4/#6/#10/#12/#14
were inspected, including closed/merged history. Only #8/#11/#13/#15 were active.
All four have exactly one canonical priority plus type, area and documented stage.
All 27 actual label names, descriptions and colors match the accepted Template
taxonomy. No labels need repair. Historical Issues and merged PRs remain untouched.
No milestones exist (all states); N/A rationale is in ROADMAP.md.

Actual mutations: no Issue, historical PR, label definition or milestone changes
were needed. The new Draft PR receives priority:P1, type:maintenance,
area:automation and stage:release at creation. This source migration neither
changes Projects/settings nor installs privileged automation. Future triage uses
`python3 -B scripts/check_github_metadata.py --repo AlexandrShapkin/codex-engineering-kit`.
The report includes active PRs and all-state history through paginated GET only.

## Verification and limits

Mandatory commands: `python3 -B scripts/check_contract.py --self-check` and
`python3 -B -m unittest discover -s tests -v`. The complete suite includes existing
private bundle/admin sync, export/rollback/collision, public distribution/fixture,
release compatibility and negative/security regressions. New cases cover policy
entrypoints, pinned provenance, rehash tampering, symlinks, local gate preservation,
metadata drift/classification and GET-only pagination. CI retains Python 3.11–3.13.
Local Python 3.14.8: 68 tests PASS, contract self-check PASS, compileall PASS.
No check runs consumer commands or substitutes smoke tests for native gates.

Real CLI probe: **BLOCKED**, not model compliance. In isolated
`/tmp/ek-issue15-probe-rlijk8pq`, root AGENTS.md matches the adopted entrypoint;
AGENTS.local.md requests explicit shell reading and a fixture-only marker. Run:
`codex exec --sandbox read-only --skip-git-repo-check -C /tmp/ek-issue15-probe-rlijk8pq`
with prompt to read repository instructions and report the local discovery marker.
Exit 1 before any model session:

```text
WARNING: proceeding, even though we could not create PATH aliases: Read-only file system (os error 30)
Error: failed to initialize in-process app-server client: Read-only file system (os error 30)
```

Full local evidence is retained in that directory's probe.log. Global configuration,
credentials and permissions were not modified. Static discovery tests pass but
cannot prove model behavior. Rerun the same isolated probe in an owner-authorized
CLI environment with writable session storage; require explicit read evidence.
Independent ChatGPT technical review and formal GitHub approval remain pending;
author verification is separate. No merge, tag, release, license or public upload.

## Cleanup, debt and rollback

Read-only inventory: filesystem 233G total, 80G available (64% used); no heavy
build needed. Existing six detached review worktrees at /tmp/ek-pr2-review,
/tmp/ek-pr2-review-002929d, /tmp/ek-pr4-review, /tmp/ek-pr4-review-3700d80,
/tmp/ek-pr4-review-6014918 and /tmp/ek-pr4-review-eae609a are clean, but are prior
unique review evidence. Preserve them; ownership/retention requires owner triage.
Existing local task branches and remote branches are preserved, including merged
PR #14 work and unverified unique commits. Other prior /tmp/ek-pr* logs/archives
are unknown evidence, preserved. Process inventory showed only the enclosing
Codex session; the probe exited. No destructive cleanup or space-reclaimed claim.
New probe fixture/log and /tmp/ek-issue15-tests.log are retained for review;
temporary unittest fixtures clean themselves. Draft branch remains active.

Debt: this task repays competing root policy activation; no new workflow engine
or dependency. Outstanding P1 work remains with owner AlexandrShapkin in #8
(consumer adoption), #11 (publication/security clearance), #13 (release
qualification), and #15 (independent migration review and environment-blocked
CLI discovery proof). Their completion requires scoped native/CI/review evidence;
no disabled gates. Source-integrity pins require explicit reviewed migration on
future Template updates, not automatic drift acceptance.

Rollback before merge: abandon this Draft without altering main; preserve review
evidence. After an authorized merge, use a reviewed revert of this bounded commit
to restore base AGENTS.md and remove adoption-only paths; repeat full native
checks/CI. No history rewriting. Subsequent admin upgrades use the retained prior
private bundle and existing exact-plan/path sync; preserve AGENTS.local.md and
technical pins. Server rollback is unnecessary because existing metadata was not
changed; the Draft's own labels need no removal.
