"""Parser for courses using spanned-table with (due ...) notes in <td> cells.

Known compatible courses: CS 152, CS 161, CS 168

HTML pattern (table.spanned-table with rowspan cells):
  <td class="" rowspan="4">
    <a href="...">Homework 1</a>
    <br/>(due Sun Sep 13)
    <br/><a>Solutions</a>
  </td>

The first <a> in the cell is the assignment link; subsequent links (Solutions,
Worksheet, etc.) are ignored. Due date is extracted via DUE_RE and
parse_due_date, same as the alpha parser but applied to <td> rather than
<div class="syllabus-item">.
"""

import re
from urllib.parse import urljoin

from .base import DUE_RE, clean, parse_due_date, split_due


def parse(soup, page_url, term_year):
    deadlines = []

    for table in soup.select("table.spanned-table"):
        for td in table.find_all("td"):
            text = clean(td.get_text(" "))
            m = DUE_RE.search(text)
            if not m:
                continue

            note = m.group(1)
            pairs = split_due(note)

            # First <a> is the primary assignment link
            a = td.find("a")
            href = a.get("href") if a else None
            base_title = clean(a.get_text()) if a else text[:60]

            # Strip trailing "(due ...)" from title if it bled in
            base_title = DUE_RE.sub("", base_title).strip()

            for suffix, raw_due in pairs:
                title = f"{base_title} ({suffix})" if suffix else base_title
                due = parse_due_date(raw_due, term_year)
                deadlines.append({
                    "title": title,
                    "raw_due": raw_due,
                    "due": due,
                    "url": urljoin(page_url, href) if href else None,
                })

    return deadlines
