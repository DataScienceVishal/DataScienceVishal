"""All network access for the profile generator.

Returns plain dicts and lists. Nothing downstream of this module touches the
network, so cards and README rendering are pure functions over the result and
can be tested with a literal.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

from config import (
    ACTIVITY_EXCLUDE,
    LANGUAGE_EXCLUDE,
    LANGUAGE_SINCE,
    LANGUAGE_SINCE_LABEL,
    USER,
)

API = "https://api.github.com"
GRAPHQL = "https://api.github.com/graphql"
TIMEOUT = 30


class GitHubError(RuntimeError):
    """The API did not give us something we can use."""


def _token() -> str:
    """Read a token from the environment.

    Actions supplies GITHUB_TOKEN. Locally, `GH_TOKEN=$(gh auth token)` works.
    Unauthenticated requests get 60/hour, which this script exceeds on the
    per-repo language calls alone, so a token is required rather than optional.
    """
    for name in ("GITHUB_TOKEN", "GH_TOKEN"):
        value = os.environ.get(name, "").strip()
        if value:
            return value
    raise GitHubError(
        "No token. Set GITHUB_TOKEN (Actions supplies it) or run "
        "GH_TOKEN=$(gh auth token) locally."
    )


def _request(url: str, *, method: str = "GET", body: dict | None = None) -> Any:
    payload = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=payload, method=method)
    request.add_header("Authorization", f"Bearer {_token()}")
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("X-GitHub-Api-Version", "2022-11-28")
    if payload is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")[:400]
        raise GitHubError(f"{method} {url} returned {error.code}: {detail}") from error
    except urllib.error.URLError as error:
        raise GitHubError(f"{method} {url} failed: {error.reason}") from error


def _paginate(path: str) -> list[dict]:
    out: list[dict] = []
    page = 1
    while True:
        batch = _request(f"{API}{path}?per_page=100&page={page}")
        if not isinstance(batch, list):
            raise GitHubError(f"{path} did not return a list")
        out.extend(batch)
        if len(batch) < 100:
            return out
        page += 1
        if page > 20:  # 2,000 repos. Something is wrong if we get here.
            raise GitHubError(f"{path} paginated past 20 pages")


def _graphql(query: str) -> dict:
    result = _request(GRAPHQL, method="POST", body={"query": query})
    if "errors" in result:
        raise GitHubError(f"GraphQL: {result['errors']}")
    return result["data"]


def _contributions() -> dict:
    """Commit contributions over the trailing year.

    Only available over GraphQL. The REST API has no equivalent.
    """
    data = _graphql(
        "{ user(login: \"%s\") { contributionsCollection {"
        " totalCommitContributions"
        " restrictedContributionsCount"
        " totalRepositoriesWithContributedCommits"
        " contributionCalendar { totalContributions }"
        " } } }" % USER
    )
    collection = data["user"]["contributionsCollection"]
    return {
        "commits": collection["totalCommitContributions"],
        "private_commits": collection["restrictedContributionsCount"],
        "active_repos": collection["totalRepositoriesWithContributedCommits"],
        "calendar_total": collection["contributionCalendar"]["totalContributions"],
    }


def _language_counts(repos: list[dict]) -> tuple[list[tuple[str, int]], int]:
    """Count repositories by primary language, within the language window.

    Returns the sorted counts and the number of repositories counted, so the
    card can print the denominator rather than only a percentage.

    See config.LANGUAGE_BY for why this counts repositories instead of bytes.
    Needs no per-repository call: the primary language is already on the
    repository object.
    """
    counts: dict[str, int] = {}
    counted = 0
    for repo in repos:
        if repo["name"] in LANGUAGE_EXCLUDE:
            continue
        if not repo.get("pushed_at") or repo["pushed_at"] < LANGUAGE_SINCE:
            continue
        language = repo.get("language")
        if not language:
            # No language detected at all, e.g. a repository of only markdown
            # or a Power BI file. Counting these as a language would invent one.
            continue
        counts[language] = counts.get(language, 0) + 1
        counted += 1
    ordered = sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))
    return ordered, counted


def _activity(repos: list[dict]) -> list[dict]:
    """Most recently pushed original repositories, newest first."""
    candidates = [
        repo
        for repo in repos
        if repo["name"] not in ACTIVITY_EXCLUDE and repo.get("pushed_at")
    ]
    candidates.sort(key=lambda repo: repo["pushed_at"], reverse=True)
    return [
        {
            "name": repo["name"],
            "url": repo["html_url"],
            "description": (repo.get("description") or "").strip(),
            "language": repo.get("language") or "",
            "pushed_at": repo["pushed_at"],
        }
        for repo in candidates
    ]


def collect() -> dict:
    """Every fact the generator needs, in one plain dict."""
    user = _request(f"{API}/users/{USER}")
    repos = _paginate(f"/users/{USER}/repos")
    languages, language_repos = _language_counts(repos)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "user": {
            "login": user["login"],
            "name": user.get("name") or user["login"],
            "public_repos": user["public_repos"],
        },
        "contributions": _contributions(),
        "languages": languages,
        "language_repos": language_repos,
        "language_since": LANGUAGE_SINCE_LABEL,
        "activity": _activity(repos),
        "repo_count_mine": len(
            [r for r in repos if r["name"] not in LANGUAGE_EXCLUDE]
        ),
    }
