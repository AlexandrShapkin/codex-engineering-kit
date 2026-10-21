# Administrative upgrades and rollback

Review the full Template source SHA, exact six managed paths and proposed diff.
Use the existing Kit admin export / sync plan / sync write workflow documented in
[SYNC.md](SYNC.md); exact path authorization and plan SHA remain mandatory.
Keep AGENTS.local.md, project docs, native CI and technical bundle pins unchanged.
Taxonomy and metadata checker are reviewed manual adoptions, not extra sync paths.
Retain the prior reviewed private bundle before updating. Rollback applies that
bundle through the same bounded admin channel and repeats native checks/review.
Initial adoption explicitly replaced only the tracked root AGENTS.md; no general
unmanaged-file overwrite permission is introduced. See [migration evidence](GOVERNANCE_AUDIT.md).

## Accepted public-source migrations

The four Kit #8 consumers have source.json records rather than bundle locks.
Use the [source-update adapter and Draft proposal procedure](SOURCE_UPDATES.md)
for those existing installations. Never feed source records to bundle sync or
manufacture locks to bypass its unmanaged collision protection.
