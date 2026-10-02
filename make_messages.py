import json
import sys
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

INPUT_FILE = "deadlines.json"
DAILY_FILE = "daily.txt"
WEEKLY_FILE = "weekly.txt"


def pretty(iso):
    """"2026-10-02" -> "Fri Oct 2" """
    d = date.fromisoformat(iso)
    return f"{d:%a %b} {d.day}"


def link_line(deadline):
    return deadline["url"] or "no link yet"


def all_deadlines(data):
    """Flatten {"classes": {name: [...]}} into one list, each with its class."""
    return [{**d, "class": name}
            for name, deadlines in data["classes"].items()
            for d in deadlines]


def grouped_by_class(deadlines):
    """Deadlines listed under their class; classes with nothing are left out."""
    lines = []
    classes = list(dict.fromkeys(d["class"] for d in deadlines))
    for name in classes:
        lines.append("")
        lines.append(name)
        for d in deadlines:
            if d["class"] == name:
                lines.append(f"• {d['title']}")
                lines.append(f"  {link_line(d)}")
    return lines


def daily_message(deadlines, today):
    tonight = [d for d in deadlines if d["due"] == today]
    if tonight:
        return "\n".join([f"📅 Due tonight ({pretty(today)})"]
                         + grouped_by_class(tonight))

    later = sorted(d["due"] for d in deadlines if d["due"] and d["due"] > today)
    if not later:
        return f"📅 Nothing due tonight ({pretty(today)}) 🎉\nNo upcoming deadlines found."
    next_day = later[0]
    lines = [f"📅 Nothing due tonight ({pretty(today)}) 🎉",
             f"Next deadline: {pretty(next_day)}"]
    return "\n".join(lines + grouped_by_class(
        [d for d in deadlines if d["due"] == next_day]))


def weekly_message(deadlines, today):
    """The 7 days after today, sorted by date across all classes."""
    start = (date.fromisoformat(today) + timedelta(days=1)).isoformat()
    end = (date.fromisoformat(today) + timedelta(days=7)).isoformat()
    week = sorted((d for d in deadlines if d["due"] and start <= d["due"] <= end),
                  key=lambda d: d["due"])

    lines = [f"🗓 This week ({pretty(start)} – {pretty(end)})", ""]
    if not week:
        lines.append("Nothing due this week 🎉")
    for d in week:
        lines.append(f"• {pretty(d['due'])} — {d['class']}: {d['title']}")
        lines.append(f"  {link_line(d)}")
    return "\n".join(lines)


def undated_warning(deadlines):
    """Deadlines whose date couldn't be read, so they don't get lost."""
    undated = [d for d in deadlines if d["due"] is None]
    if not undated:
        return ""
    lines = ["", "", "⚠️ Couldn't read the date for:"]
    for d in undated:
        lines.append(f"• {d['class']}: {d['title']} (\"{d['raw_due']}\")")
    return "\n".join(lines)


if __name__ == "__main__":
    # Optional: python make_messages.py 2026-10-05  (pretend today is that date)
    today = sys.argv[1] if len(sys.argv) > 1 else datetime.now(ZoneInfo("America/Los_Angeles")).date().isoformat()

    with open(INPUT_FILE) as f:
        deadlines = all_deadlines(json.load(f))

    warning = undated_warning(deadlines)
    with open(DAILY_FILE, "w") as f:
        f.write(daily_message(deadlines, today) + warning)
    with open(WEEKLY_FILE, "w") as f:
        f.write(weekly_message(deadlines, today) + warning)
    print(f"Wrote {DAILY_FILE} and {WEEKLY_FILE} for {today}")
