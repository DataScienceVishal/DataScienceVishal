"""Tests for the marker rewriting.

This is the module that edits the README in place, so the properties worth
pinning are that it changes what it should and nothing else.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import readme_blocks as rb  # noqa: E402

FACTS = {
    "generated_at": "2026-09-08T12:00:00+00:00",
    "user": {"login": "u", "name": "U", "public_repos": 35},
    "contributions": {
        "commits": 545,
        "private_commits": 0,
        "active_repos": 13,
        "calendar_total": 600,
    },
    "languages": [("Python", 5), ("TypeScript", 1)],
    "language_repos": 6,
    "language_since": "Jan 2026",
    "activity": [
        {
            "name": "twicerun",
            "url": "https://github.com/u/twicerun",
            "description": "An audit of nondeterminism.",
            "language": "Python",
            "pushed_at": "2026-09-08T13:36:11Z",
        },
        {
            "name": "lesion-split",
            "url": "https://github.com/u/lesion-split",
            "description": "",
            "language": "Python",
            "pushed_at": "2026-09-03T15:39:45Z",
        },
    ],
    "repo_count_mine": 34,
}


def test_replaces_only_between_markers():
    text = (
        "keep me above\n"
        "<!-- profile:activity -->\nold junk\n<!-- /profile:activity -->\n"
        "keep me below\n"
    )
    out = rb.replace_block(text, "activity", "NEW")
    assert "keep me above" in out
    assert "keep me below" in out
    assert "old junk" not in out
    assert "NEW" in out


def test_is_idempotent():
    text = "<!-- profile:activity -->\nx\n<!-- /profile:activity -->\n"
    once = rb.replace_block(text, "activity", "SAME")
    twice = rb.replace_block(once, "activity", "SAME")
    assert once == twice


def test_missing_marker_is_an_error():
    with pytest.raises(rb.MarkerError, match="No <!-- profile:activity"):
        rb.replace_block("nothing here", "activity", "x")


def test_duplicate_marker_is_an_error():
    text = (
        "<!-- profile:activity --><!-- /profile:activity -->"
        "<!-- profile:activity --><!-- /profile:activity -->"
    )
    with pytest.raises(rb.MarkerError, match="appears 2 times"):
        rb.replace_block(text, "activity", "x")


def test_one_block_does_not_disturb_another():
    text = (
        "<!-- profile:activity -->\nA\n<!-- /profile:activity -->\n"
        "<!-- profile:stamp -->\nB\n<!-- /profile:stamp -->\n"
    )
    out = rb.replace_block(text, "activity", "CHANGED")
    assert "CHANGED" in out
    assert "\nB\n" in out


def test_activity_table_shape():
    table = rb.activity_table(FACTS)
    lines = table.splitlines()
    assert lines[0].startswith("| repository ")
    assert len(lines) == 4  # header, separator, two rows
    assert "[twicerun](https://github.com/u/twicerun)" in table
    assert "8 Sep 2026" in table


def test_missing_description_is_marked_not_blank():
    assert "_no description_" in rb.activity_table(FACTS)


def test_pipe_in_description_is_escaped():
    facts = {**FACTS, "activity": [
        {**FACTS["activity"][0], "description": "a | b"},
    ]}
    assert "a \\| b" in rb.activity_table(facts)


def test_long_description_is_truncated():
    facts = {**FACTS, "activity": [
        {**FACTS["activity"][0], "description": "x" * 200},
    ]}
    row = rb.activity_table(facts).splitlines()[2]
    assert "…" in row
    assert len(row) < 160


def test_truncation_lands_on_a_word_boundary():
    """A row ending 'the test set…' reads; one ending 'the test se…' does not."""
    long_text = "Splitting HAM10000 by image leaks thirty eight percent of " \
                "the test set into training which is a great deal of leakage"
    facts = {**FACTS, "activity": [
        {**FACTS["activity"][0], "description": long_text},
    ]}
    row = rb.activity_table(facts).splitlines()[2]
    shown = row.split("|")[2].strip().rstrip("…")
    # The visible text must be a prefix of the original ending at a word break.
    assert long_text.startswith(shown)
    assert long_text[len(shown)] == " "


def test_empty_activity_does_not_emit_a_headerless_table():
    assert rb.activity_table({**FACTS, "activity": []}) == "_No recent activity._"


def test_row_limit_is_respected():
    many = [dict(FACTS["activity"][0], name=f"r{i}") for i in range(20)]
    table = rb.activity_table({**FACTS, "activity": many}, rows=3)
    assert len(table.splitlines()) == 5  # header, separator, three rows


def test_render_fills_every_block():
    text = (
        "<!-- profile:activity -->\n\n<!-- /profile:activity -->\n"
        "<!-- profile:stamp -->\n\n<!-- /profile:stamp -->\n"
    )
    out = rb.render(text, FACTS)
    assert "twicerun" in out
    assert "8 Sep 2026" in out
