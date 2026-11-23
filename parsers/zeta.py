"""Parser for DS100-style week tables with label-*-due syllabus items.

Known compatible courses: DS 100 (Data C100)

HTML pattern (one <table> per week, rows per day):
  <tr>
    <td>Mon, Sep 07</td>              <!-- date column -->
    <td>...</td>                      <!-- lecture column -->
    <td>...</td>                      <!-- discussion column -->
    <td>                              <!-- assignments column -->
      <div class="syllabus-item">
        <strong class="label label-homework-due">Homework 1 Due</strong>
        <a href="...">Assignment title</a>
      </div>
    </td>
  </tr>

The date in the first <td> of each row is the exact due date.
Title is the <strong> text with trailing " Due" stripped.
Duplicates (same title + due) are dropped — the same assignment can appear
in multiple rows when rowspan isn't used.
"""

import re
from urllib.parse import urljoin

from .base import clean, NAMED_DATE_RE, MONTHS
from datetime import date


def _parse_ds100_date(text, term_year):
    """Parse "Mon, Sep 07" or "Fri, Dec 4" into ISO date."""
    m = NAMED_DATE_RE.search(text)
    if not m:
        return None
    month = MONTHS[m.group(1).lower()[:3]]
    day = int(m.group(2))
    try:
        return date(term_year, month, day).isoformat()
    except ValueError:
        return None


_DUE_LABEL_RE = re.compile(r"\blabel-(homework-due|project-due|lab-due|exam-due)\b")


def parse(soup, page_url, term_year):
    deadlines = []
    seen = set()  # (title, due) dedup

    for table in soup.find_all("table"):
        for tr in table.find_all("tr"):
            cells = tr.find_all("td")
            if len(cells) < 2:
                continue
            raw_date = clean(cells[0].get_text())
            due = _parse_ds100_date(raw_date, term_year)

            for cell in cells[1:]:
                for item in cell.select("div.syllabus-item"):
                    strong = item.find("strong", class_=_DUE_LABEL_RE)
                    if not strong:
                        continue

                    raw_title = clean(strong.get_text())
                    title = re.sub(r"\s+Due$", "", raw_title, flags=re.IGNORECASE).strip()

                    a = item.find("a")
                    href = a.get("href") if a else None

                    key = (title, due)
                    if key in seen:
                        continue
                    seen.add(key)

                    deadlines.append({
                        "title": title,
                        "raw_due": raw_date,
                        "due": due,
                        "url": urljoin(page_url, href) if href else None,
                    })

    return deadlines
