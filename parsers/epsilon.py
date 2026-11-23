"""Parser for EECS 189-style <dl> schedule with <strong class="label-due">.

Known compatible courses: EECS 189

HTML pattern (definition list):
  <dt>Fri Sep 18</dt>
  <dd><strong class="label label-due">Homework 1 Part 1 due</strong></dd>

The due date is in the preceding <dt>; the assignment title is the <strong>
text with trailing " due" stripped. No assignment links are present in the
HTML — no url is emitted.
"""

import re

from .base import clean, NAMED_DATE_RE, MONTHS
from datetime import date


def _parse_named_date(text, term_year):
    """Parse "Mon Sep 14" or "Fri Dec 4" into ISO date."""
    m = NAMED_DATE_RE.search(text)
    if not m:
        return None
    month = MONTHS[m.group(1).lower()[:3]]
    day = int(m.group(2))
    try:
        return date(term_year, month, day).isoformat()
    except ValueError:
        return None


def parse(soup, page_url, term_year):
    deadlines = []

    for dd in soup.find_all("dd"):
        strong = dd.find("strong", class_=re.compile(r"\blabel-due\b"))
        if not strong:
            continue

        raw_title = clean(strong.get_text())
        # Strip trailing " due" from "Homework 1 Part 1 due"
        title = re.sub(r"\s+due$", "", raw_title, flags=re.IGNORECASE).strip()

        dt = dd.find_previous_sibling("dt")
        raw_due = clean(dt.get_text()) if dt else ""
        due = _parse_named_date(raw_due, term_year)

        deadlines.append({
            "title": title,
            "raw_due": raw_due,
            "due": due,
            "url": None,
        })

    return deadlines
