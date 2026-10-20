# Kit stage map

Navigation only; acceptance remains in the linked GitHub Issues and PRs.
Shared governance comes from the [canonical interface](../.github/DEVELOPMENT_INTERFACE.md).
Issue numbers below belong to AlexandrShapkin/codex-engineering-kit.

| Stage ID | Goal | Dependencies | Owning Issues | Completion evidence |
| --- | --- | --- | --- | --- |
| foundation | Source contract, offline CLI and independent channels | None | #1, #3, #5, #7, #9 (closed) | PRs #2/#4/#6/#10 merged |
| distribution | Reviewed private/public distribution boundaries | foundation | #11 | PR #12 merged; publication/license authority still blocked |
| release | Independent release qualification and canonical governance | foundation; distribution before publication | #13, #15 | PR #14 merged; #15 requires exact-head CI and independent acceptance |
| rollout | Individually reviewed consumer adoption | accepted governance/release source and distribution review | #8 | Separate consumer Draft PRs, native gates and review |

Milestones: deliberate N/A. No confirmed version/date or accepted milestone
assignment is established by the proposed v0.1.0 qualification. Live inventory on
2026-10-21 contains no milestones; do not invent placeholders. Reassess when the
owner confirms a deliverable. No historical relabeling is needed.
