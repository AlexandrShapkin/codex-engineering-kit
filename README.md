# Codex Engineering Kit

Practical, independently usable development utilities for AI coding agents.
Requires Python 3.11+; Git observation requires POSIX and Git. No installation,
consumer manifest or Project Template dependency is required.

```sh
python3 /path/to/codex-engineering-kit/scripts/ek.py status --root /path/to/repository
python3 /path/to/codex-engineering-kit/scripts/ek.py context --root /path/to/repository
python3 /path/to/codex-engineering-kit/scripts/ek.py doctor
```

`status` observes bounded Git metadata without hooks, filters or network access.
Unstaged tracked changes can remain UNVERIFIED; this is not a deletion-safety check.
`context` lists useful entrypoint paths; `doctor` reports installed tool availability.
Neither executes discovered project instructions. Optional skills in skills/ explain
practical context acquisition, verification and PR closeout.

Use `git diff`, `gh pr checks`, `just`, native tests and existing security tooling
directly for everyday operations. Repository structure and common agent instruction
templates belong to Project Template. The Kit does not manage consumer governance,
contracts, synchronized files, source-update proposals or distribution approval.
Retired machinery and its tests remain recoverable in Git history. Accepted evidence
JSON in docs/ is historical provenance, not a current adoption requirement.

Checks: `python3 -B -m unittest discover -s tests -v` and
`python3 -B -m compileall -q engineering_kit scripts tests`.
MIT; retain LICENSE and provenance notices.
