"""Fetch deadline data from all registered courses and write deadlines.json.

To add a course: append a row to CLASSES.
To add a new HTML structure: create parsers/beta.py etc., then reference it here.
"""

import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from parsers import alpha
from parsers.base import get_soup

# (display_name, url, parser_module)
CLASSES = [
    ("CS 61A",  "https://cs61a.org/fa26/",  alpha),
    ("Data C8", "https://data8.org/fa26/",  alpha),
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

    for name, url, parser in CLASSES:
        soup = get_soup(url)
        deadlines = parser.parse(soup, url, term_year_from_url(url))
        output["classes"][name] = deadlines
        print(f"  {name}: {len(deadlines)} deadlines")

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"Wrote {OUTPUT_FILE}")
