"""Explicit anonymous public GitHub GET. Fixed endpoints, no redirects or tokens."""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

MAX_BYTES = 64 * 1024
MAX_SECONDS = 10
REPO_RE = re.compile(r"[A-Za-z0-9_.-]{1,100}/[A-Za-z0-9_.-]{1,100}\Z")
SHA_RE = re.compile(r"[0-9a-fA-F]{40,64}\Z")


class GithubReadError(ValueError):
    pass


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise GithubReadError("GitHub redirect refused")


def get_public(repo: str, resource: str, identifier: str) -> dict[str, object]:
    if not REPO_RE.fullmatch(repo) or ".." in repo.split("/"):
        raise GithubReadError("invalid repository name")
    if resource not in ("issue", "pr", "run", "commit"):
        raise GithubReadError("unsupported GitHub resource")
    if resource == "commit":
        if not SHA_RE.fullmatch(identifier):
            raise GithubReadError("expected complete Git commit SHA")
        fragment = "commits/" + identifier.lower()
    else:
        if not re.fullmatch(r"[1-9][0-9]{0,11}", identifier):
            raise GithubReadError("expected bounded positive numeric identifier")
        fragment = {"issue": "issues/", "pr": "pulls/",
                    "run": "actions/runs/"}[resource] + identifier
    url = "https://api.github.com/repos/" + repo + "/" + fragment
    request = urllib.request.Request(
        url, headers={"Accept": "application/vnd.github+json",
                      "User-Agent": "codex-engineering-kit/0.1"},
        method="GET")
    # No env proxies (may contain credentials), automatic auth, or redirect.
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}), _NoRedirect())
    try:
        with opener.open(request, timeout=MAX_SECONDS) as response:
            if response.status != 200:
                raise GithubReadError("GitHub request unsuccessful")
            if "json" not in response.headers.get("Content-Type", "").lower():
                raise GithubReadError("non-JSON GitHub response")
            data = response.read(MAX_BYTES + 1)
            if len(data) > MAX_BYTES:
                raise GithubReadError("GitHub response too large")
    except GithubReadError:
        raise
    except (OSError, urllib.error.URLError, ValueError) as exc:
        raise GithubReadError(
            "public GitHub GET failed (private resources and redirects unsupported)") from exc
    try:
        item = json.loads(data)
    except (ValueError, UnicodeError) as exc:
        raise GithubReadError("invalid GitHub JSON response") from exc
    if not isinstance(item, dict):
        raise GithubReadError("unexpected GitHub response shape")
    public_link = "https://github.com/" + repo
    if resource in ("issue", "pr"):
        expected = int(identifier)
        if item.get("number") != expected:
            raise GithubReadError("GitHub identity mismatch")
        return {"resource": resource, "repo": repo, "number": expected,
                "state": str(item.get("state", ""))[:32],
                "title": str(item.get("title", ""))[:300],
                "url": public_link + ("/issues/" if resource == "issue"
                                      else "/pull/") + identifier}
    if resource == "run":
        if item.get("id") != int(identifier):
            raise GithubReadError("GitHub identity mismatch")
        return {"resource": resource, "repo": repo, "id": int(identifier),
                "status": str(item.get("status", ""))[:32],
                "conclusion": str(item.get("conclusion", ""))[:32],
                "head_sha": str(item.get("head_sha", ""))[:64],
                "url": public_link + "/actions/runs/" + identifier}
    actual = str(item.get("sha", ""))
    if actual.lower() != identifier.lower():
        raise GithubReadError("GitHub identity mismatch")
    return {"resource": resource, "repo": repo, "sha": actual.lower(),
            "url": public_link + "/commit/" + actual.lower()}
