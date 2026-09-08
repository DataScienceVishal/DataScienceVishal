"""Render the stats cards as SVG.

Pure functions over the dict from github_data. No network, no clock.

Two constraints shape the output. GitHub's README sanitiser strips <style>
elements, so every visual property is a presentation attribute. And there are
no webfonts, so the font stack has to be one the reader already has.

Stars and followers are absent on purpose. Neither measures the work, and at
this account's numbers both would understate it.
"""

from __future__ import annotations

from xml.sax.saxutils import escape

from config import LANGUAGE_BARS

FONT = (
    "-apple-system,BlinkMacSystemFont,Segoe UI,Noto Sans,Helvetica,Arial,sans-serif"
)

# GitHub's own surface colours, so the cards sit flush with the page.
THEMES = {
    "light": {
        "bg": "#ffffff",
        "border": "#d1d9e0",
        "text": "#1f2328",
        "muted": "#59636e",
        "accent": "#0969da",
        "track": "#eaeef2",
    },
    "dark": {
        "bg": "#0d1117",
        "border": "#3d444d",
        "text": "#f0f6fc",
        "muted": "#9198a1",
        "accent": "#4493f8",
        "track": "#21262d",
    },
}

# Linguist colours. Anything unlisted falls back to the theme accent.
LANGUAGE_COLOURS = {
    "Python": "#3572A5",
    "TypeScript": "#3178c6",
    "JavaScript": "#f1e05a",
    "Jupyter Notebook": "#DA5B0B",
    "R": "#198CE7",
    "Vue": "#41b883",
    "C": "#555555",
    "C++": "#f34b7d",
    "Ruby": "#701516",
    "Svelte": "#ff3e00",
    "SQL": "#e38c00",
}


def _thousands(value: int) -> str:
    return f"{value:,}"


def _text(x: int, y: int, content: str, *, size: int, fill: str,
          weight: str = "400", anchor: str = "start") -> str:
    return (
        f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">'
        f"{escape(content)}</text>"
    )


def _frame(width: int, height: int, theme: dict, title: str, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="{escape(title)}">'
        f"<title>{escape(title)}</title>"
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" '
        f'rx="6" fill="{theme["bg"]}" stroke="{theme["border"]}"/>'
        f"{body}</svg>"
    )


def stats_card(facts: dict, variant: str) -> str:
    """Contribution figures. Four numbers, each with a plain-English label."""
    theme = THEMES[variant]
    contributions = facts["contributions"]

    public = contributions["commits"]
    private = contributions["private_commits"]
    # "of those" has to sit directly under the number it divides, or the card
    # reads as 33 of 13.
    rows = [
        (_thousands(public + private), "commit contributions, past year"),
        (_thousands(contributions["active_repos"]), "repositories committed to"),
        (_thousands(facts["user"]["public_repos"]), "public repositories"),
        (_thousands(facts["repo_count_mine"]), "of those, original work"),
    ]

    width, height = 460, 190
    body = [
        _text(24, 36, "Contribution activity", size=15, fill=theme["text"],
              weight="600"),
        _text(24, 56, "Trailing 12 months, public and private", size=11,
              fill=theme["muted"]),
    ]
    y = 92
    for value, label in rows:
        body.append(_text(24, y, value, size=17, fill=theme["accent"],
                          weight="600"))
        body.append(_text(96, y, label, size=12, fill=theme["muted"]))
        y += 26

    return _frame(width, height, theme, "Contribution activity", "".join(body))


def language_card(facts: dict, variant: str) -> str:
    """Primary language of each repository, counted, within the window.

    Counted rather than byte-weighted. See config.LANGUAGE_BY: .ipynb files
    embed their output images, so bytes measure matplotlib output and not the
    author.

    The subtitle states the window and the denominator. A windowed figure
    presented as an all-time one would be a misrepresentation whichever way it
    happened to fall.
    """
    theme = THEMES[variant]
    languages = facts["languages"][:LANGUAGE_BARS]
    counted = facts.get("language_repos", 0)
    since = facts.get("language_since", "")

    width = 460
    height = 78 + max(len(languages), 1) * 28

    body = [
        _text(24, 36, "Primary language, by repository", size=15,
              fill=theme["text"], weight="600"),
        _text(24, 56,
              f"{counted} repositories pushed since {since}, counted not "
              f"byte-weighted", size=11, fill=theme["muted"]),
    ]

    if not languages:
        body.append(_text(24, 90, "No data", size=12, fill=theme["muted"]))
        return _frame(width, height, theme, "Primary language", "".join(body))

    # Denominator is every counted repository, so the visible bars may sum to
    # less than 100% when the tail is longer than LANGUAGE_BARS.
    total = counted or sum(count for _, count in facts["languages"]) or 1
    bar_x, bar_width = 150, 210
    y = 86

    for name, count in languages:
        share = count / total
        colour = LANGUAGE_COLOURS.get(name, theme["accent"])
        filled = max(2, round(bar_width * share))
        body.append(_text(24, y + 11, name, size=12, fill=theme["text"]))
        body.append(
            f'<rect x="{bar_x}" y="{y}" width="{bar_width}" height="14" '
            f'rx="7" fill="{theme["track"]}"/>'
        )
        body.append(
            f'<rect x="{bar_x}" y="{y}" width="{filled}" height="14" '
            f'rx="7" fill="{colour}"/>'
        )
        label = f"{count} of {total}"
        body.append(
            _text(width - 24, y + 11, label, size=11, fill=theme["muted"],
                  anchor="end")
        )
        y += 28

    return _frame(width, height, theme, "Primary language by repository",
                  "".join(body))


def render_all(facts: dict) -> dict[str, str]:
    """Every card, keyed by the filename it belongs in."""
    out: dict[str, str] = {}
    for variant in THEMES:
        out[f"stats-{variant}.svg"] = stats_card(facts, variant)
        out[f"languages-{variant}.svg"] = language_card(facts, variant)
    return out
