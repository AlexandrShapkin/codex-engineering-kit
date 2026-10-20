# CLI observation (v0.1 Draft)

The CLI provides local, read-only developer information as JSON. It does not
install dependencies, access GitHub, run product-native checks or clean files.

```sh
python3 -B scripts/ek.py doctor
python3 -B scripts/ek.py status --root /path/to/repository
python3 -B scripts/ek.py context --root /path/to/repository
python3 -B scripts/ek.py checks --profile rustcraft
```

`status` reports the repository root, full HEAD, branch, staged and untracked
file counts. It uses fixed Git commands with no shell, hooks, fsmonitor,
global/system configuration, lazy fetch or transport. Stdout is capped at
128 KiB per command; stderr is discarded. Each command has a 10-second
deadline. Failure terminates its dedicated process group, closes the pipe and
reaps the direct child. POSIX and an already installed, trusted Git executable
on PATH are required; unsupported platforms fail closed. Descendants that
deliberately leave the dedicated process group are outside this cleanup bound.

**Unstaged tracked changes remain UNVERIFIED.** Comparing working-tree contents
can execute repository-defined clean filters. Partial clones with missing
objects return a controlled failure rather than fetching. A false
`known_pending_changes` value therefore does not prove a clean working tree.

`context` lists existing known entrypoint paths without loading their contents.
`doctor` checks binary availability without launching or installing tools.
`checks` lists pinned product-native requirement markers without executing them.

## Decision: defer GitHub GET

Issue #3 makes public GitHub GET optional. It is excluded from v0.1: the local
commands meet the required scope without maintaining an HTTP transport,
credential policy or process-global signal deadline. `github-get` is not a
supported subcommand and fails argument parsing before any work starts.
The previous HTTP client and its signal/timer management have been removed.
There is no fallback to `gh`, a connector or another privileged GitHub tool.

GitHub evidence must be obtained separately through an already available,
explicitly authorized tool. No tool installation or additional access is
implied. Without that evidence, exact-head CI and GitHub state remain
UNVERIFIED; these local observations do not replace native checks, independent
review or merge/runtime authorization.
