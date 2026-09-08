"""Tests for SVG rendering.

The cards go through GitHub's image sanitiser, which strips <style> and any
script, so the tests assert the output stays inside what survives that.
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cards  # noqa: E402
from test_readme_blocks import FACTS  # noqa: E402


@pytest.mark.parametrize("variant", ["light", "dark"])
def test_cards_are_well_formed_xml(variant):
    for svg in (cards.stats_card(FACTS, variant),
                cards.language_card(FACTS, variant)):
        ET.fromstring(svg)  # raises on malformed output


@pytest.mark.parametrize("variant", ["light", "dark"])
def test_no_style_or_script_elements(variant):
    """GitHub strips these, so relying on them would break the cards silently."""
    for svg in (cards.stats_card(FACTS, variant),
                cards.language_card(FACTS, variant)):
        assert "<style" not in svg
        assert "<script" not in svg


def _visible_text(svg: str) -> str:
    """Only the text a reader sees, not attribute values."""
    root = ET.fromstring(svg)
    ns = "{http://www.w3.org/2000/svg}"
    return " ".join(
        (node.text or "") for node in root.iter(f"{ns}text")
    ).lower()


def test_stats_card_shows_contributions_not_vanity_metrics():
    svg = cards.stats_card(FACTS, "light")
    visible = _visible_text(svg)
    assert "545" in visible
    assert "commit contributions" in visible
    assert "follower" not in visible
    assert "stars" not in visible


def test_private_commits_are_added_to_the_total():
    facts = {**FACTS, "contributions": {**FACTS["contributions"],
                                        "private_commits": 55}}
    assert "600" in cards.stats_card(facts, "light")


def test_language_card_states_its_window_and_denominator():
    """A windowed figure that does not say so is a misrepresentation."""
    visible = _visible_text(cards.language_card(FACTS, "light"))
    assert "jan 2026" in visible
    assert "6 repositories" in visible
    assert "counted not byte-weighted" in visible


def test_language_counts_are_over_all_repos_not_the_visible_bars():
    """Six bars drawn from a nine-language tail must divide by the full count."""
    facts = {
        **FACTS,
        "languages": [(f"L{i}", 1) for i in range(9)],
        "language_repos": 9,
    }
    visible = _visible_text(cards.language_card(facts, "light"))
    assert "1 of 9" in visible
    assert "1 of 6" not in visible


def test_empty_languages_renders_a_card_rather_than_crashing():
    svg = cards.language_card({**FACTS, "languages": [],
                               "language_repos": 0}, "light")
    ET.fromstring(svg)
    assert "No data" in svg


def test_text_is_xml_escaped():
    facts = {**FACTS, "languages": [("C++ & <b>", 1)]}
    svg = cards.language_card(facts, "light")
    ET.fromstring(svg)
    assert "&amp;" in svg
    assert "<b>" not in svg


def test_render_all_produces_four_named_files():
    out = cards.render_all(FACTS)
    assert set(out) == {
        "stats-light.svg", "stats-dark.svg",
        "languages-light.svg", "languages-dark.svg",
    }


def test_original_work_row_follows_its_denominator():
    """"of those" must sit under public repositories, not under a stray number."""
    visible = _visible_text(cards.stats_card(FACTS, "light"))
    assert visible.index("public repositories") < visible.index("of those")
    assert visible.index("repositories committed to") < visible.index(
        "public repositories"
    )
