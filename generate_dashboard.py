#!/usr/bin/env python3
"""Generate AI Overview dashboard HTML from WakaTime + Hermes data."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.hermes_db import get_yesterday_range, fetch_sessions, aggregate_stats
from lib.wakatime import fetch_summary
from lib.dashboard_template import render_dashboard

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "archive")


def generate():
    start_dt, end_dt, yesterday = get_yesterday_range()
    start_ts = start_dt.timestamp()
    end_ts = end_dt.timestamp()
    date_str = yesterday.strftime("%Y-%m-%d")
    display_range = yesterday.strftime("%b %-d, %Y")

    waka = fetch_summary(date_str)
    sessions = fetch_sessions(start_ts, end_ts)
    stats = aggregate_stats(sessions) if sessions else {}

    total_time = waka["total_text"] if waka else "0 mins"
    categories = waka["categories"] if waka else []
    editors = waka["editors"] if waka else []

    # WakaTime AI stats (available in free plan)
    ai_input = waka.get("ai_input_tokens", 0) if waka else 0
    ai_output = waka.get("ai_output_tokens", 0) if waka else 0
    ai_prompts = waka.get("ai_prompts", 0) if waka else 0

    html = render_dashboard(
        date_range=display_range,
        total_time=total_time,
        categories=categories,
        editors=editors,
        ai_input=ai_input,
        ai_output=ai_output,
        ai_prompts=ai_prompts,
        hermes_input=stats.get("total_input", 0),
        hermes_output=stats.get("total_output", 0),
        hermes_cache=stats.get("total_cache_read", 0),
        session_count=stats.get("session_count", 0),
    )

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, f"ai-overview-{date_str}.html")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Dashboard saved: {filepath}")
    return filepath


if __name__ == "__main__":
    path = generate()
    if path:
        print(f"OK: {path}")
    else:
        print("No data")
        sys.exit(1)
