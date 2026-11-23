"""Parser for Berkeley courses using the standard syllabus-item table layout.

Known compatible courses: CS 61A, Data C8

HTML pattern:
  <div class="syllabus-item">
    <strong class="label label-TYPE">Lab 0</strong>
    <a href="...">Getting Started (due Wed 9/2)</a>
  </div>

Deadlines are identified by a "(... due ...)" note in the item text.
Multi-date items (e.g. "due Fri 10/2; checkpoint Mon 9/28") are expanded
into one entry per date.
"""

from urllib.parse import urljoin
from .base import DUE_RE, clean, split_due, parse_due_date


def parse(soup, page_url, term_year):
    deadlines = []
    for item in soup.select("div.syllabus-item"):
        item_text = clean(item.get_text(" ", strip=True))
        m = DUE_RE.search(item_text)
        if not m:
            continue

        note = clean(m.group(1))

        label = item.find("strong", class_="label")
        label_text = clean(label.get_text(" ", strip=True)) if label else ""

        name = item_text
        if label_text:
            name = name.replace(label_text, "", 1)
        name = clean(DUE_RE.sub("", name))

        # cs61a: label is "Lab 0", name is "Getting Started" → title = "Lab 0 Getting Started"
        # data8: label is "Lab 1", name is "Lab 1" → title = "Lab 1" (no duplicate)
        if label_text and label_text.lower() not in name.lower():
            title = f"{label_text} {name}".strip()
        else:
            title = name or label_text

        link = item.find("a")
        href = link.get("href") if link else None
        url = urljoin(page_url, href) if href else None

        for suffix, date_str in split_due(note):
            deadlines.append({
                "title": f"{title} ({suffix})" if suffix else title,
                "raw_due": date_str,
                "due": parse_due_date(date_str, term_year),
                "url": url,
            })
    return deadlines
