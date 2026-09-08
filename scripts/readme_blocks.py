"""Rewrite the marked regions of README.md and nothing else.

The marker convention is the one already used in trail-scorer-audit and
lesion-split:

    <!-- profile:activity -->
    generated content
    <!-- /profile:activity -->

Two rules the tests pin down. Text outside a marker pair is hand-written and
must survive untouched. And a marker that is missing, duplicated or unbalanced
is an error, because the alternative is a workflow that reports success while
silently updating nothing.

Dates are absolute rather than relative. "3 days ago" would change on every
scheduled run and commit a diff on days when nothing happened; "6 Sep 2026"
changes only when a push actually does.
"""

from __future__ import annotations

import re
from datetime import datetime

from config import ACTIVITY_ROWS


class MarkerError(RuntimeError):
    """A marker pair is missing, duplicated or out of order."""


def _pattern(name: str) -> re.Pattern[str]:
    return re.compile(
        rf"(<!--\s*profile:{re.escape(name)}\s*-->)"
        rf"(.*?)"
        rf"(<!--\s*/profile:{re.escape(name)}\s*-->)",
        re.DOTALL,
    )


def replace_block(text: str, name: str, content: str) -> str:
    """Swap the body of one marker pair. Raises if the pair is not unique."""
    pattern = _pattern(name)
    matches = pattern.findall(text)
    if not matches:
        raise MarkerError(
            f"No <!-- profile:{name} --> ... <!-- /profile:{name} --> pair in README"
        )
    if len(matches) > 1:
        raise MarkerError(f"profile:{name} appears {len(matches)} times, expected once")

    def substitute(match: re.Match[str]) -> str:
        return f"{match.group(1)}\n{content.strip()}\n{match.group(3)}"

    return pattern.sub(substitute, text, count=1)


def _shorten(text: str, limit: int) -> str:
    """Trim to a whole word, so a row does not end mid-word before the ellipsis."""
    if len(text) <= limit:
        return text
    cut = text[: limit - 1]
    if " " in cut:
        cut = cut[: cut.rindex(" ")]
    return cut.rstrip(" ,.;:") + "…"


def _pretty_date(iso: str) -> str:
    """2026-09-08T13:36:11Z -> 8 Sep 2026."""
    parsed = datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ")
    return f"{parsed.day} {parsed.strftime('%b %Y')}"


def activity_table(facts: dict, rows: int = ACTIVITY_ROWS) -> str:
    """Recently pushed original repositories, as a markdown table."""
    entries = facts["activity"][:rows]
    if not entries:
        return "_No recent activity._"

    lines = [
        "| repository | what it is | last push |",
        "| --- | --- | --- |",
    ]
    for entry in entries:
        description = entry["description"] or "_no description_"
        description = _shorten(description, 96)
        description = description.replace("|", "\\|")
        lines.append(
            f"| [{entry['name']}]({entry['url']}) "
            f"| {description} "
            f"| {_pretty_date(entry['pushed_at'])} |"
        )
    return "\n".join(lines)


def stamp(facts: dict) -> str:
    """One-line provenance note under the generated sections."""
    generated = datetime.strptime(
        facts["generated_at"], "%Y-%m-%dT%H:%M:%S+00:00"
    )
    return (
        f"<sub>Generated from the GitHub API on "
        f"{generated.day} {generated.strftime('%b %Y')}. "
        f"See <a href=\"scripts/\">scripts/</a>.</sub>"
    )


def render(text: str, facts: dict) -> str:
    """Apply every generated block to the README text."""
    text = replace_block(text, "activity", activity_table(facts))
    text = replace_block(text, "stamp", stamp(facts))
    return text
