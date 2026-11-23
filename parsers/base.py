"""Shared utilities for all parsers: HTTP fetch, text cleaning, due-date parsing."""

import re
import requests
from bs4 import BeautifulSoup
from datetime import date


# "(... due ...)" note, e.g. "(due Wed 9/2)" or "(Checkpoint due 10/2, Entire project due 10/9)"
DUE_RE = re.compile(r"\(([^)]*?\bdue\s+[^)]+)\)", re.IGNORECASE)

# One fragment like "due Thu 9/17" or "Checkpoint due 10/2"
KEYWORD_DUE_RE = re.compile(r"^(.*?)\bdue\s+(.+)$", re.IGNORECASE)

# Keyword-prefixed fragment after the first, e.g. "checkpoint 1 Fri 10/16"
CHECKPOINT_RE = re.compile(r"^([a-z]+(?:\s+\d+)?)\s+(.+)$", re.IGNORECASE)

# "9/2", "Wed 9/2"
NUMERIC_DATE_RE = re.compile(r"\b(\d{1,2})/(\d{1,2})\b")

# "Fri Aug 28", "September 1"
NAMED_DATE_RE = re.compile(
    r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{1,2})\b",
    re.IGNORECASE,
)

MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5,  "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


_soup_cache: dict = {}


def get_soup(url):
    """Fetch and parse a URL, caching within this process run."""
    if url not in _soup_cache:
        print(f"Fetching {url}")
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        _soup_cache[url] = BeautifulSoup(r.text, "html.parser")
    return _soup_cache[url]


def clean(text):
    return text.replace("\xa0", " ").strip()


def split_due(note):
    """Split a due note into (suffix, date_str) pairs.

    "due Thu 9/10; checkpoint Thu 9/3"
      -> [("", "Thu 9/10"), ("checkpoint", "Thu 9/3")]
    """
    parts = [p.strip() for p in re.split(r"[;,]", note) if p.strip()]
    result = []
    for i, part in enumerate(parts):
        m = KEYWORD_DUE_RE.match(part)
        if m:
            result.append((m.group(1).strip().lower(), m.group(2).strip()))
            continue
        m = CHECKPOINT_RE.match(part)
        if i > 0 and m:
            result.append((m.group(1).strip().lower(), m.group(2).strip()))
        else:
            result.append(("", part))
    return result


def parse_due_date(raw_due, term_year):
    """Parse a raw due string into an ISO date, or None if unreadable."""
    m = NUMERIC_DATE_RE.search(raw_due)
    if m:
        month, day = int(m.group(1)), int(m.group(2))
    else:
        m = NAMED_DATE_RE.search(raw_due)
        if not m:
            return None
        month, day = MONTHS[m.group(1).lower()[:3]], int(m.group(2))
    try:
        return date(term_year, month, day).isoformat()
    except ValueError:
        return None
