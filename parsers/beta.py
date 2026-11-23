"""Parser for the CS 61B-style dedicated deadlines page.

Known compatible courses: CS 61B

HTML pattern (ul#deadline-checklist):
  <li class="deadline-checklist-item" data-finalized="true|false">
    <span class="deadline-checklist-kind">Homework</span>
    <a class="deadline-checklist-title" href="...">HW1: Setup</a>  <!-- span if not yet released -->
    <time class="deadline-checklist-date" datetime="2026/08/28">Fri, Aug 28</time>
  </li>

The datetime attribute is already a full machine-readable date (YYYY/MM/DD or YYYY-MM-DD),
so no date-string parsing is needed. term_year is accepted for interface consistency but unused.
"""

from datetime import date
from urllib.parse import urljoin

from .base import clean


def _normalize_date(raw):
    """'2026/08/28' or '2026-08-28' -> '2026-08-28', or None if malformed."""
    try:
        return date.fromisoformat(raw.replace('/', '-')).isoformat()
    except (ValueError, AttributeError):
        return None


def parse(soup, page_url, term_year):
    deadlines = []
    for li in soup.select('li.deadline-checklist-item'):
        kind_el = li.select_one('.deadline-checklist-kind')
        title_el = (li.select_one('a.deadline-checklist-title')
                    or li.select_one('span.deadline-checklist-title'))
        time_el = li.select_one('time.deadline-checklist-date')

        if not (kind_el and title_el and time_el):
            continue

        kind_text = clean(kind_el.get_text())
        title_text = clean(title_el.get_text())

        # Prepend kind when the title doesn't already contain it, e.g.:
        # "Project 0: Particle Simulator" keeps as-is; "1A: Deques" -> "Project 1A: Deques"
        if kind_text.lower() in title_text.lower():
            title = title_text
        else:
            title = f"{kind_text} {title_text}"

        href = title_el.get('href') if title_el.name == 'a' else None
        raw_due = time_el.get('datetime', '')

        deadlines.append({
            'title': title,
            'raw_due': raw_due,
            'due': _normalize_date(raw_due),
            'url': urljoin(page_url, href) if href else None,
        })
    return deadlines
