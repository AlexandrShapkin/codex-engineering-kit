# CLI observation (v0.1 Draft)

The CLI is explicitly **read-only**: no install, GitHub writes, task runner, worktree creation, destructive cleanup or consumer-native execution.

\`\`\`sh
python3 -B scripts/ek.py doctor
python3 -B scripts/ek.py status --root /path/to/repository
python3 -B scripts/ek.py context --root /path/to/repository
python3 -B scripts/ek.py checks --profile rustcraft

# The ONLY command with network: explicit anonymous public GitHub GET
python3 -B scripts/ek.py github-get issue OWNER/REPO 123
python3 -B scripts/ek.py github-get pr OWNER/REPO 123
python3 -B scripts/ek.py github-get run OWNER/REPO 123456
python3 -B scripts/ek.py github-get commit OWNER/REPO FULL_SHA
\`\`\`

Outputs JSON. \`status\` invokes only fixed local Git introspection commands, with Git optional locks disabled, no external Git configuration, no fsmonitor and no hooks. It uses only index-vs-HEAD and untracked-path metadata, returning counts without copying filenames into logs. **Unstaged tracked changes remain UNVERIFIED**: content-comparing Git operations such as `git status` and `git diff-files` can execute untrusted repository clean filters. \`context\` lists known source entrypoint names; \`doctor\` checks binary availability without invoking or installing them. \`checks\` reports product-native requirement **markers only**; it never executes them.

\`github-get\` is the only command that makes HTTPS requests. It only accepts syntactically checked repo IDs and exact bounded resource identifiers, fixes host to \`api.github.com\`, limits response and timeout, refuses redirects/proxy-derived credentials and reads **anonymous public** data only. Private repositories are not supported in this version. It never reads local GitHub tokens or authentication files, and it does not send authorization headers. Results are treated as untrusted data.

These checks do not replace CI/security/independent review, and do not authorize merge, runtime activation, deploy or privileged MCP tools.
