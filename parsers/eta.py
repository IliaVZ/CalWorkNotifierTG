"""Parser for courses with (due ...) notes in any <td> cell.

Known compatible courses: CS 184, CS 186

HTML pattern (table with per-row or rowspan cells):
  <td class="hw1" rowspan="...">
    <a href="...">Homework 1 Checkpoint</a><br/>(due 09/13)
  </td>

Same logic as delta but searches all tables, not only table.spanned-table.
Deduplicates by (title, due) so rowspan cells counted twice are dropped.
"""

import re
from urllib.parse import urljoin

from .base import DUE_RE, clean, parse_due_date, split_due


def parse(soup, page_url, term_year):
    deadlines = []
    seen = set()

    for td in soup.find_all("td"):
        text = clean(td.get_text(" "))
        m = DUE_RE.search(text)
        if not m:
            continue

        note = m.group(1)
        pairs = split_due(note)

        a = td.find("a")
        href = a.get("href") if a else None
        base_title = clean(a.get_text()) if a else text[:60]
        base_title = DUE_RE.sub("", base_title).strip()
        if not base_title:
            continue

        for suffix, raw_due in pairs:
            title = f"{base_title} ({suffix})" if suffix else base_title
            due = parse_due_date(raw_due, term_year)
            key = (title, due)
            if key in seen:
                continue
            seen.add(key)
            deadlines.append({
                "title": title,
                "raw_due": raw_due,
                "due": due,
                "url": urljoin(page_url, href) if href else None,
            })

    return deadlines
