# Codex Engineering Kit

Shared agent instructions, offline validation and future reusable development tools for Codex projects.

**Status:** initial v0.1 **Draft source proposal**. Private repository, no license selected. No runtime, merge, device, secret or installation authority.

The v0.1 source imports the exact normative workflow and shared agent block from the four unmerged agent-unification proposals. This snapshot has not been accepted or integrated into their main branches.

| Source | Draft PR | Exact SHA |
| --- | --- | --- |
| Codex Smart | [#176](https://github.com/AlexandrShapkin/codex-smart/pull/176) | `982749389c23615a5fa65fbb3b99c01d0a94de1d` |
| RelayForge | [#80](https://github.com/AlexandrShapkin/relayforge/pull/80) | `ca8904fec6c1b57eabf9b971fca8ecf815131d12` |
| Assistant Hub | [#60](https://github.com/AlexandrShapkin/assistant-hub/pull/60) | `cb98ed5945e7a844990cd0f944ed235f3478ff63` |
| RustCraft | [#36](https://github.com/AlexandrShapkin/rustcraft/pull/36) | `09e5b3ecd482db53b6919c329ab348e230572f94` |

The copied `contract/DEVELOPMENT_INTERFACE.md` preserves its original references to Draft PRs and old per-project paths for verifiable provenance. No new authority is inferred from this source snapshot.

## First slice

- `contract/`: the canonical shared interface and common AGENTS.md fragment.
- `engineering_kit/contract.py`: offline source checker. Product-specific gate markers live as data in `profiles/products.json`, not in executable if/else branches.
- `skills/`: three instruction-only skills.
- `tests/` and read-only GitHub Actions Python 3.11–3.13.

Offline usage after a reviewed checkout:

```sh
python3 -B scripts/check_contract.py --self-check
python3 -B -m unittest discover -s tests -v
python3 -B scripts/check_contract.py --root /path/to/consumer --profile rustcraft
```

A contract check neither runs the consumer native checks nor verifies product functionality. All source consumers retain their own CI and security gates.

The optional CLI provides local `status`, `context`, `doctor` and `checks`
observations. See [CLI usage and limits](docs/CLI.md). GitHub GET is deferred
from v0.1; the CLI has no network command or GitHub-tool fallback.

Versioned offline bundles and explicitly authorized sync are documented in [bundle adoption, update and rollback](docs/SYNC.md). GitHub retrieval, network updaters and consumer templates remain outside this slice. No general orchestrator, MCP server, credentials, Codex global config, RelayForge grants, deployment or automatic external mutation is included.

Administrative workflow ownership and the opt-in format-2 template channel are
specified in [SYNC](docs/SYNC.md#administrative-channel-format-2-proposed-compatibility-extension).
Existing v0.1 contract files remain unchanged legacy snapshots for compatibility;
new administrative policy is canonical in `AlexandrShapkin/project-template`.
