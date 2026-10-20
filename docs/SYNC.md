# Versioned offline bundles (format 1)

Requires POSIX, Python 3.11+ and Git for export only; no dependencies or network.
A version is the full upstream Git commit SHA, not a mutable tag. The bundle
is a single JSON file containing a manifest and UTF-8 content, with SHA-256
for every managed file. Export reads regular tracked files from that commit,
never the working tree. Export reuses the bounded POSIX Git reader (128 KiB per
command, 10-second deadline, no hooks/filters/lazy fetch/transport); missing
objects fail closed. Input bundle, lock and target reads are capped at 1 MiB
each. Source provenance remains in README and the contracts.

## Export and adopt

From a reviewed Kit checkout, replace COMMIT with a reviewed full 40-character
SHA. The output must not already exist. Retain the bundle for rollback.

```sh
python3 -B scripts/ek.py bundle --source . --revision COMMIT \
  --profile minimal --output /tmp/kit-bundle.json
python3 -B scripts/ek.py sync plan --root /path/to/consumer \
  --bundle /tmp/kit-bundle.json
```

Review the bundle contents, `changes` array and `plan_sha256`. Plan performs
no writes and does not create missing directories. For write, provide the
returned digest and one `--allow PATH` for **each** changed path, including
`.engineering-kit/lock.json`. No glob, directory permission or implicit approval
is accepted. The digest binds the plan to the absolute normalized consumer path
and its filesystem device/inode identity; moving or replacing the directory
requires a new plan, and tokens cannot be transferred between consumers.
For example, append all individually reviewed paths to:

```sh
python3 -B scripts/ek.py sync write --root /path/to/consumer \
  --bundle /tmp/kit-bundle.json --plan-sha256 PLAN_DIGEST \
  --allow .engineering-kit/PROFILE.md
# Incomplete permission sets are rejected before writing.
```

The command never edits AGENTS.md, local rules, native CI or global settings.
All managed paths are under `.engineering-kit/`. The lock records format,
profile, upstream SHA and installed file hashes. There is no implicit discovery
or activation: an owner can separately add a reviewed reference from their
existing AGENTS.md to `.engineering-kit/PROFILE.md` and the reference contracts.
Their historical cross-project paths are provenance, not installed entrypoints;
resolve references under `.engineering-kit/` explicitly. Local rules and stronger
product gates always take precedence; bundled skills are reference material,
not automatically installed or executed skills.

Profiles carry the same reference contract/skills plus a small PROFILE.md:
`minimal` (local rules first), `backend` (API/data/native tests),
`infrastructure` (drift/rollback, no deploy authority), `research`
(methods/provenance/data preservation). They install no tools or CI recipes.

## Update and rollback

Export a bundle from the next reviewed commit and run plan, review, then write
with the new exact digest and path set. Removed managed files are explicit
`delete` operations. Rollback uses the same flow with the retained older bundle;
there is no automatic downgrade prohibition or remote version resolution.
A second plan for an already installed bundle is empty.

Any missing/edited managed file, untracked collision, malformed manifest,
duplicate JSON key, excessive JSON nesting, checksum mismatch, unsafe path or symlink in the root/path
aborts validation. Never delete the lock to bypass a conflict. Preserve edits
and reconcile deliberately outside this command, then rerun plan. Unmanaged
files, including other files in `.engineering-kit/`, are preserved; directories
are not pruned. Lock integrity is checked structurally and installed hashes
are verified; it is not cryptographically authenticated.

## Trust and failure limits

Hashes detect corruption; they do not authenticate the publisher. Obtain the
bundle through a trusted channel and compare its full upstream SHA and contents
with the reviewed source. Export can use any local commit: it does not establish
GitHub acceptance, a signature, licensing or public redistribution permission.
No consumer repositories are modified by the Kit's own tests or CI.

Use a quiescent local checkout with no concurrent writers, hostile filesystem
actors or symlink replacement. Symlinks (including dangling ones and ancestor
components) are refused at validation/access. This is not a sandbox against
concurrent filesystem attacks. Writes use exclusive temporary files and atomic
replacement **per file**, with lock last; the multi-file operation is not a
transaction and is not crash/power-loss durable. An I/O failure may leave a
partial update; preserve the checkout and restore affected files and lock from
a verified Git snapshot/backup before retrying. Do not auto-reset or auto-delete
conflicts. Keep consumer changes in a bounded branch and commit the reviewed
installed files/lock together. Installation/live use and independent technical
acceptance remain separate from offline tests.
