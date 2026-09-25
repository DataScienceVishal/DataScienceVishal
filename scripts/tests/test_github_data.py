"""Tests for the activity table's filtering.

The table answers "what is being worked on now", and it reads pushed_at to do
it. A bulk metadata pass can reset pushed_at across old repositories without
anyone touching their code, which is how 2024 coursework reached the top five.
The creation-date floor is what stops that, so it is the thing worth pinning.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import github_data as gd  # noqa: E402


def _repo(name, pushed, created):
    return {
        "name": name,
        "pushed_at": pushed,
        "created_at": created,
        "html_url": f"https://github.com/u/{name}",
        "description": "",
        "language": "Python",
    }


def test_an_old_repo_with_a_fresh_push_stays_out():
    repos = [
        _repo("notebook-2024", "2026-09-11T00:00:00Z", "2024-03-20T00:00:00Z"),
        _repo("current", "2026-09-01T00:00:00Z", "2026-08-26T00:00:00Z"),
    ]
    names = [r["name"] for r in gd._activity(repos)]
    assert names == ["current"]


def test_a_repo_missing_created_at_stays_out():
    repos = [_repo("unknown", "2026-09-11T00:00:00Z", None)]
    assert gd._activity(repos) == []


def test_ordering_is_still_newest_push_first():
    repos = [
        _repo("older-push", "2026-09-01T00:00:00Z", "2026-08-01T00:00:00Z"),
        _repo("newer-push", "2026-09-20T00:00:00Z", "2026-08-01T00:00:00Z"),
    ]
    names = [r["name"] for r in gd._activity(repos)]
    assert names == ["newer-push", "older-push"]
