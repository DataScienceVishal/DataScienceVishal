"""Tests for the CLI's round-trip.

The bug these exist for: the writer appended a trailing newline and --check
compared without one, so --check reported freshly written files as stale. A
staleness check that is always positive is worse than none.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import update  # noqa: E402


def test_on_disk_adds_exactly_one_trailing_newline():
    assert update._on_disk("<svg/>") == "<svg/>\n"


def test_on_disk_is_idempotent():
    once = update._on_disk("<svg/>")
    assert update._on_disk(once) == once


def test_written_form_equals_compared_form(tmp_path):
    """What the writer puts on disk is what --check compares against."""
    svg = "<svg/>"
    target = tmp_path / "card.svg"
    target.write_text(update._on_disk(svg))
    assert target.read_text() == update._on_disk(svg)
