#!/usr/bin/env python3
"""Generate daily receipt HTML from Hermes Agent state.db."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.hermes_db import get_yesterday_range, fetch_sessions, aggregate_stats
from lib.template import render_receipt

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "archive")


def format_tokens(n):
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def format_duration(seconds):
    if not seconds:
        return "00:00"
    hours = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    if hours > 0:
        return f"{hours}h {mins:02d}m"
    return f"{mins}m"


def generate():
    start_dt, end_dt, yesterday = get_yesterday_range()
    start_ts = start_dt.timestamp()
    end_ts = end_dt.timestamp()
    date_str = yesterday.strftime("%Y-%m-%d")
    display_date = yesterday.strftime("%B %-d, %Y")

    sessions = fetch_sessions(start_ts, end_ts)
    if not sessions:
        print(f"No sessions for {date_str}")
        return None

    stats = aggregate_stats(sessions)

    total_tokens = stats["total_input"] + stats["total_output"]

    from collections import Counter

    models = Counter(s["model"] for s in sessions if s["model"])
    sources = Counter(s["source"] for s in sessions if s["source"])

    # Top tools across all sessions
    tool_counter = Counter()
    for s in sessions:
        from lib.hermes_db import fetch_tool_calls

        tool_counter.update(fetch_tool_calls(s["id"]))

    html = render_receipt(
        date_str=date_str,
        display_date=display_date,
        total_tokens=total_tokens,
        total_input=stats["total_input"],
        total_output=stats["total_output"],
        session_count=stats["session_count"],
        total_msgs=stats["total_msgs"],
        total_tools=stats["total_tools"],
        models=models,
        sources=sources,
        sessions=sessions,
        top_tools=tool_counter.most_common(5),
        format_tokens=format_tokens,
        format_duration=format_duration,
    )

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, f"joye-receipt-{date_str}.html")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Saved: {filepath}")

    # Regenerate index.html
    try:
        import generate_index
        generate_index.generate()
    except Exception as e:
        print(f"index.html regeneration skipped: {e}")

    return filepath


if __name__ == "__main__":
    path = generate()
    if path:
        print(f"OK: {path}")
    else:
        print("No data")
        sys.exit(1)
