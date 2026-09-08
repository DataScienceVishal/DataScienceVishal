#!/usr/bin/env python3
"""Regenerate the dynamic parts of the profile.

    python scripts/update.py            # fetch, write cards, rewrite README
    python scripts/update.py --check    # fail if the committed output is stale
    python scripts/update.py --facts f  # render from a saved facts file, no network

--check regenerates into memory and exits non-zero if that differs from what is
committed. It is a local convenience, not a CI gate: the activity table goes
stale whenever a push lands in any other repository, so gating pull requests on
it would fail for reasons unrelated to the change under review.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import cards  # noqa: E402
import readme_blocks  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
ASSETS = ROOT / "assets"


def _on_disk(svg: str) -> str:
    """The exact bytes a card is stored as.

    Used by both the writer and --check. Two spellings of "the file contents"
    is how --check came to report freshly written files as stale.
    """
    return svg if svg.endswith("\n") else svg + "\n"


def _load_facts(path: str | None) -> dict:
    if path:
        return json.loads(Path(path).read_text())
    import github_data  # imported late so --facts needs no token

    return github_data.collect()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                       help="exit non-zero if committed output is stale")
    parser.add_argument("--facts", help="read facts from a JSON file")
    parser.add_argument("--dump-facts", help="write fetched facts to a JSON file")
    args = parser.parse_args()

    facts = _load_facts(args.facts)
    if args.dump_facts:
        Path(args.dump_facts).write_text(json.dumps(facts, indent=2) + "\n")

    rendered_readme = readme_blocks.render(README.read_text(), facts)
    rendered_cards = cards.render_all(facts)

    if args.check:
        stale: list[str] = []
        if rendered_readme != README.read_text():
            stale.append("README.md")
        for name, svg in rendered_cards.items():
            existing = ASSETS / name
            if not existing.exists() or existing.read_text() != _on_disk(svg):
                stale.append(f"assets/{name}")
        if stale:
            print("Stale, run python scripts/update.py:", ", ".join(stale))
            return 1
        print("Generated output is current.")
        return 0

    ASSETS.mkdir(exist_ok=True)
    README.write_text(rendered_readme)
    for name, svg in rendered_cards.items():
        (ASSETS / name).write_text(_on_disk(svg))

    print(f"Wrote README.md and {len(rendered_cards)} cards.")
    print(f"  languages: {', '.join(n for n, _ in facts['languages'][:6])}")
    print(f"  activity rows: {len(facts['activity'])} available")
    return 0


if __name__ == "__main__":
    sys.exit(main())
