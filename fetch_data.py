"""Fetch deadline data from all registered courses and write deadlines.json.

To add a course:    append a row to CLASSES.
To add a structure: create parsers/beta.py etc., then reference it here.
To filter a course: pass a filter_fn as the 4th element (None = keep all).
"""

import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from parsers import alpha, beta
from parsers.base import get_soup

# ---------------------------------------------------------------------------
# Per-course filters
# ---------------------------------------------------------------------------

# CS 47B: required subset of CS 61B assignments.
# Source: https://fa26.datastructur.es/policies/cs47b/
# Review at the start of each semester — assignment numbers/names can shift.
_CS47B_HWS = frozenset({
    "Homework HW1: Setup",
    "Homework HW2: Java Intro",
    "Homework HW5: BSTMaps",
    "Homework HW6: Midterm Review",
    "Homework HW7: HashMaps",
    "Homework HW9: Final Review",
})
# Project 4 has un-numbered sub-items (Checkpoint, Design Doc) sitting between
# the numbered parts in the CS 61B deadlines list.
_CS47B_PROJECT_PARTS = frozenset({"Project Checkpoint", "Project Design Doc"})


def cs47b_filter(d):
    t = d["title"]
    return (
        t in _CS47B_HWS
        or t in _CS47B_PROJECT_PARTS
        or bool(re.match(r"Project [45]", t))
    )


# ---------------------------------------------------------------------------
# Course registry
# ---------------------------------------------------------------------------

_61B_URL = "https://fa26.datastructur.es/deadlines/"

# (display_name, url, parser_module, filter_fn | None)
CLASSES = [
    ("CS 61A",  "https://cs61a.org/fa26/",  alpha, None),
    ("Data C8", "https://data8.org/fa26/",  alpha, None),
    ("CS 61B",  _61B_URL,                   beta,  None),
    ("CS 47B",  _61B_URL,                   beta,  cs47b_filter),
]

OUTPUT_FILE = "deadlines.json"


def term_year_from_url(url):
    """Infer the term year from a URL slug like fa26 or sp27."""
    m = re.search(r"[a-z]{2}(\d{2})\b", url)
    if m:
        return 2000 + int(m.group(1))
    return datetime.now(ZoneInfo("America/Los_Angeles")).year


if __name__ == "__main__":
    today = datetime.now(ZoneInfo("America/Los_Angeles")).date().isoformat()
    output = {"generated": today, "classes": {}}

    for name, url, parser, filter_fn in CLASSES:
        soup = get_soup(url)
        deadlines = parser.parse(soup, url, term_year_from_url(url))
        if filter_fn:
            deadlines = [d for d in deadlines if filter_fn(d)]
        output["classes"][name] = deadlines
        print(f"  {name}: {len(deadlines)} deadlines")

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"Wrote {OUTPUT_FILE}")
