# Engineering Kit

Kit owns source-only technical mechanisms: offline observation, validation,
versioned exports and explicitly bounded synchronization. It is not a runtime
executor. Read [CLI.md](CLI.md), [SYNC.md](SYNC.md) and
[PUBLIC_DISTRIBUTION.md](PUBLIC_DISTRIBUTION.md) for technical contracts.

The shared lifecycle belongs only to the [Template interface](../.github/DEVELOPMENT_INTERFACE.md).
Native gates and limits live in [AGENTS.local.md](../AGENTS.local.md).
Legacy contract snapshots are retained unchanged for existing consumers/checkers;
their embedded lifecycle is not active Kit administrative policy.

The compatibility surface includes CLI arguments/results, export/sync safety,
bundle/lock formats, technical skills and profiles. Proposed compatible patches
are >=0.1.0,<0.2.0; no release is declared. Formats and full source pins remain
independent of SemVer. [RELEASING.md](RELEASING.md) records Kit artifact applicability,
targets, compatibility and qualification; [release notes](RELEASE_NOTES_v0.1.0.md)
record behavior and impact. No tag, release or publication is authorized.

[ROADMAP.md](ROADMAP.md) navigates owning Issues; [GOVERNANCE_AUDIT.md](GOVERNANCE_AUDIT.md)
records this migration and remaining evidence.
