# Kit-specific agent rules

Consult [docs/PROJECT.md](docs/PROJECT.md) for task-relevant technical context.
The active shared lifecycle is discovered through root AGENTS.md;
contract/ snapshots remain frozen compatibility/provenance.

# Engineering Kit agent instructions

The Kit maintains the common, source-only agent contract. It is not a Codex Smart runtime or privileged executor.

Discover actual root, HEAD, branch, dirty state and owning GitHub Issue before editing. Keep changes in bounded branches and Draft PRs.

Native checks are `python3 -B scripts/check_contract.py --self-check` and `python3 -B -m unittest discover -s tests -v`, plus exact-head GitHub CI. Do not execute consumer commands through this checker. Never install dependencies, fetch secrets, change global Codex config, use RDC, run a production build, deploy, merge or modify GitHub administration without the required explicit authority.

Review source provenance and exact proposed changes, test negative cases, and report full HEAD/CI/review evidence. Cleanup requires read-only inventory first; preserve active work, untracked unknown data, Draft PR branches and unique evidence. MIT LICENSE applies to owner-controlled source. The owner authorized public source visibility after safety/rights checks and independent review/approved merge; this does not authorize tags, Releases, public bundles or deployment.
