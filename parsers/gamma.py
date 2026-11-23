"""Parser for CS 61C-style Bootstrap table with badge due dates.

Known compatible courses: CS 61C

HTML pattern (table with rowspan cells):
  <td class="align-middle" rowspan="...">
    <a href="...">Homework 1: Number Representation</a>
    <span class="badge border border-faded">Due 9/01</span>
  </td>

Multi-part projects produce separate entries via badge text prefix, e.g.:
  <span class="badge ...">A: Due 9/25</span>  → title "(A)"
  <span class="badge ...">B: Due 10/08</span> → title "(B)"

No separate deadline page; all deadlines are in one table on the main page.
"""

import re
from urllib.parse import urljoin

from .base import clean, parse_due_date

# "A: Due 9/25" or "Due 9/25"
_BADGE_RE = re.compile(r"^(?:([A-Za-z]):\s*)?due\s+(.+)$", re.IGNORECASE)


def parse(soup, page_url, term_year):
    deadlines = []
    seen = set()  # (title, due) dedup for identical rowspan cells

    for badge in soup.find_all("span", class_="badge"):
        text = clean(badge.get_text())
        m = _BADGE_RE.match(text)
        if not m:
            continue

        part, raw_date = m.group(1), m.group(2).strip()
        due = parse_due_date(raw_date, term_year)

        td = badge.find_parent("td")
        if not td:
            continue
        a = td.find("a")
        if a:
            title = clean(a.get_text())
            url = urljoin(page_url, a.get("href")) if a.get("href") else None
        else:
            # Fallback: use all text in the td minus the badge
            badge.extract()
            title = clean(td.get_text())
            url = None

        if part:
            title = f"{title} ({part})"

        raw_due = f"{part}: Due {raw_date}" if part else f"Due {raw_date}"
        key = (title, due)
        if key in seen:
            continue
        seen.add(key)

        deadlines.append({
            "title": title,
            "raw_due": raw_due,
            "due": due,
            "url": url,
        })

    return deadlines
