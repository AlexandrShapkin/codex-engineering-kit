# CLI observation (v0.1 Draft)

Source-only, explicitly bounded developer queries. No dependency installation, privileged MCP, GitHub writes, product-native command execution or destructive cleanup.

\`\`\`sh
python3 -B scripts/ek.py doctor
python3 -B scripts/ek.py status --root /path/to/repository
python3 -B scripts/ek.py context --root /path/to/repository
python3 -B scripts/ek.py checks --profile rustcraft

# The ONLY network command, explicit anonymous public GitHub GET:
python3 -B scripts/ek.py github-get issue OWNER/REPO 123
python3 -B scripts/ek.py github-get pr OWNER/REPO 123
python3 -B scripts/ek.py github-get run OWNER/REPO 123456
python3 -B scripts/ek.py github-get commit OWNER/REPO FULL_SHA
\`\`\`

JSON output. \`status\` uses fixed local Git metadata commands with \`GIT_NO_LAZY_FETCH=1\`, \`GIT_ALLOW_PROTOCOL=""\`, no global/system configuration, no hooks/fsmonitor and optional locks disabled. It captures stdout in a **128 KiB bounded stream**, drops stderr without buffering, enforces a 10-second deadline and terminates the dedicated Git process group on errors/timeouts, including descendants still holding stdout, and reaps the direct child. POSIX is required; unsupported platforms fail closed. No Git fetch/transport or user-repository programs are authorized.

Only staged and untracked file counts are reported. **Unstaged tracked changes remain UNVERIFIED** because content-comparing Git operations can execute repository-defined clean filters. Partial clones with missing objects return a controlled failure, not a fetch.

\`context\` lists known source files, \`doctor\` reports binary availability without launching or installing tools, and \`checks\` lists product-native verification markers without executing commands.

\`github-get\` only supports anonymous public GitHub API requests. The host is fixed to \`api.github.com\` over TLS with \`http.client\` (no environment proxy, redirect following, automatic credentials or token files). Every GET has **one interruptible 10-second deadline** covering DNS/handshake, response headers, chunk-size/trailers and body reads (POSIX main thread only; refuses use when SIGALRM is blocked, pending, assigned a custom handler or claimed by an active timer); the response must be JSON, at most 64 KiB. It rejects incomplete HTTP and excessively nested JSON with controlled errors. The POSIX SIGALRM interrupt is process-global. Non-main-thread/non-POSIX callers and callers with blocked/pending SIGALRM, a non-default handler or an existing ITIMER_REAL alarm fail closed; it does not claim universal portability or containment of native resolver implementations. No attempt is made to access private repositories.

Product-native tests and exact-head CI, security review, permissions and runtime evidence are separate requirements.
