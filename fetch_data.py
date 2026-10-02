import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import date, datetime
from zoneinfo import ZoneInfo
from urllib.parse import urljoin

# Class name (as shown in the message) -> schedule page.
CLASSES = {
    "CS 61A": "https://cs61a.org/fa26/",
    "Data C8": "https://data8.org/fa26/",
    # Not supported by parse_theme_a yet:
    # "CS 61B": "https://fa26.datastructur.es/",
    # "CS 189": "https://eecs189.org/fa26/",
    # "Data 100": "https://ds100.org/fa26/",
}

OUTPUT_FILE = "deadlines.json"

# Matches a parenthesized note containing the word "due" and captures its
# inside, e.g.
#   "Getting Started (due Wed 9/2)" -> "due Wed 9/2"            (cs61a)
#   "Project 1 (Checkpoint due 10/2, Entire project due 10/9)"
#       -> "Checkpoint due 10/2, Entire project due 10/9"       (data8)
DUE_RE = re.compile(r"\(([^)]*?\bdue\s+[^)]+)\)", re.IGNORECASE)

# One part of a note written as "<keyword> due <date>", e.g.
# "due Thu 9/17" or "Checkpoint due 10/2".
KEYWORD_DUE_RE = re.compile(r"^(.*?)\bdue\s+(.+)$", re.IGNORECASE)

# A due note may bundle several dates separated by ";" or ",", e.g.
# "Thu 9/17; checkpoint Thu 9/10" or
# "Fri 10/23; checkpoint 1 Fri 10/16; checkpoint 2 Wed 10/21".
# Every part after the first is prefixed by a keyword ("checkpoint", "checkpoint 1").
CHECKPOINT_RE = re.compile(r"^([a-z]+(?:\s+\d+)?)\s+(.+)$", re.IGNORECASE)


def split_due(note):
    """Split a due note into (suffix, date_str) pairs.

    The main deadline gets suffix "" ; extra parts keep their keyword,
    e.g. ("checkpoint", "Thu 9/10") or ("entire project", "10/9").
    """
    parts = [p.strip() for p in re.split(r"[;,]", note) if p.strip()]
    result = []
    for i, part in enumerate(parts):
        match = KEYWORD_DUE_RE.match(part)
        if match:
            result.append((match.group(1).strip().lower(), match.group(2).strip()))
            continue
        match = CHECKPOINT_RE.match(part)
        if i > 0 and match:
            result.append((match.group(1).strip().lower(), match.group(2).strip()))
        else:
            result.append(("", part))
    return result


# All the fa26 sites write dates without a year.
TERM_YEAR = 2026

MONTHS = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
          "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}

# "9/2", "Wed 9/2"
NUMERIC_DATE_RE = re.compile(r"\b(\d{1,2})/(\d{1,2})\b")
# "Fri Aug 28", "Tue Sep 01", "September 1"
NAMED_DATE_RE = re.compile(r"\b(" + "|".join(MONTHS) + r")[a-z]*\.?\s+(\d{1,2})\b",
                           re.IGNORECASE)


def parse_due_date(raw_due):
    """Turn a raw due string into an ISO date ("2026-09-02"), or None if it
    can't be read (e.g. the "19/16" typo seen on one page)."""
    match = NUMERIC_DATE_RE.search(raw_due)
    if match:
        month, day = int(match.group(1)), int(match.group(2))
    else:
        match = NAMED_DATE_RE.search(raw_due)
        if not match:
            return None
        month, day = MONTHS[match.group(1).lower()[:3]], int(match.group(2))
    try:
        return date(TERM_YEAR, month, day).isoformat()
    except ValueError:
        return None


def get_soup(url):
    print(f"Fetching {url}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def clean(text):
    return text.replace("\xa0", " ").strip()


def parse_theme_a(soup, page_url):
    """Berkeley course theme A (cs61a, data8).

    Each schedule entry is a <div class="syllabus-item"> holding a
    <strong class="label label-TYPE"> (e.g. "Lab 0") and a name element.
    The name element is an <a> once the assignment is released, or a plain
    <span> while it is still upcoming (data8 sometimes uses neither, just
    bare text). A deadline is any item whose text has a "(... due ...)" note.
    """
    deadlines = []
    for item in soup.select("div.syllabus-item"):
        item_text = clean(item.get_text(" ", strip=True))
        match = DUE_RE.search(item_text)
        if not match:
            continue

        note = clean(match.group(1))

        label = item.find("strong", class_="label")
        label_text = clean(label.get_text(" ", strip=True)) if label else ""

        # name = the item text minus the label prefix and the "(due ...)" note
        name = item_text
        if label_text:
            name = name.replace(label_text, "", 1)
        name = clean(DUE_RE.sub("", name))

        # data8 repeats the label inside the name ("Lab 1" / "Lab 1 (due ...)"),
        # cs61a does not ("Lab 0" / "Getting Started (due ...)").
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
                "due": parse_due_date(date_str),
                "url": url,
            })
    return deadlines


def fetch_data(url):
    soup = get_soup(url)
    return parse_theme_a(soup, url)


def upcoming(deadlines, today):
    """Keep deadlines due today or later, sorted by date.

    Deadlines whose date couldn't be read (due is None) are kept at the end,
    so they get noticed instead of silently disappearing.
    """
    dated = sorted((d for d in deadlines if d["due"] and d["due"] >= today),
                   key=lambda d: d["due"])
    undated = [d for d in deadlines if d["due"] is None]
    return dated + undated


if __name__ == "__main__":
    today = datetime.now(ZoneInfo("America/Los_Angeles")).date().isoformat()
    output = {"generated": today, "classes": {}}
    for name, url in CLASSES.items():
        deadlines = upcoming(fetch_data(url), today)
        output["classes"][name] = deadlines
        print(f"  {name}: {len(deadlines)} upcoming")

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"Wrote {OUTPUT_FILE}")
