"""Tunables for the profile generator.

Everything here is a judgement call about what the profile should say, kept
apart from the code that fetches and renders it.
"""

from __future__ import annotations

USER = "DataScienceVishal"

# The repository holding this README. Excluded from the activity block, because
# "Vishal pushed to his profile README" is not a signal about anything.
PROFILE_REPO = "DataScienceVishal"

# Repositories that are course material, tutorial follow-alongs or vendored
# third-party trees. Cloned rather than forked, so the GitHub API does not flag
# them and no automatic rule can find them.
#
# Excluded from language totals and from the activity block. Deliberately NOT
# excluded from the public repository count, which stays as GitHub reports it.
NOT_MY_WORK = {
    # Ed Donner's "LLM Engineering" course. 458 MB, of which 64 MB is Jupyter
    # Notebook. Byte-weighted language totals including this report the profile
    # as ~95% notebook, which describes the course author, not this account.
    "AI_Engineering_Core_Track",
}

# Superseded by ai-professional-twin. Kept public for history, but it should not
# take a slot in a five-row "recent work" table.
SUPERSEDED = {
    "my-ai-resume",
}

ACTIVITY_EXCLUDE = NOT_MY_WORK | SUPERSEDED | {PROFILE_REPO}
LANGUAGE_EXCLUDE = NOT_MY_WORK | {PROFILE_REPO}

# Rows in the self-updating activity table.
ACTIVITY_ROWS = 5

# Bars in the language card.
LANGUAGE_BARS = 6

# The language card counts repositories by primary language rather than
# weighting by bytes.
#
# Byte weighting is broken for this account. A .ipynb stores its output images
# as base64 inside the document, so a notebook with a few plots outweighs an
# entire Python service. Byte-weighted, these repositories read as 92% Jupyter
# Notebook, which measures matplotlib rather than anything about the author.
#
# Dropping notebooks from the byte total would be the easy fix and the wrong
# one: the 2026 analytics repositories genuinely are notebooks, and silently
# removing a category to improve a chart is not a defensible measurement.
# Counting repositories is immune to the inflation and needs no exclusion.
LANGUAGE_BY = "repositories"

# The language window. Stated on the card, because a windowed figure presented
# as an all-time one is a misrepresentation regardless of how flattering it is.
LANGUAGE_SINCE = "2026-01-01T00:00:00Z"
LANGUAGE_SINCE_LABEL = "Jan 2026"
