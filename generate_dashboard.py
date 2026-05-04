#!/usr/bin/env python3
"""Generate AI Overview dashboard from WakaTime weekly data."""

import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.wakatime import fetch_summary
from lib.dashboard_template import render_dashboard

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "archive")
MELBOURNE_TZ = timezone(timedelta(hours=10))


def fmt_tokens(n):
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def fmt_additions(n):
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def get_week_range():
    """Return last 7 days range (yesterday minus 6 days)."""
    now_melb = datetime.now(timezone.utc).astimezone(MELBOURNE_TZ)
    yesterday = now_melb - timedelta(days=1)
    week_start = yesterday - timedelta(days=6)
    return week_start, yesterday


def generate():
    week_start, week_end = get_week_range()
    start_str = week_start.strftime("%Y-%m-%d")
    end_str = week_end.strftime("%Y-%m-%d")
    date_range = f"{week_start.strftime('%b %-d')} - {week_end.strftime('%b %-d, %Y')}"

    # Fetch WakaTime weekly data
    # The API returns daily summaries; we aggregate
    total_seconds = 0
    total_ai_in = 0
    total_ai_out = 0
    total_prompts = 0
    total_additions = 0
    total_deletions = 0
    categories_agg = {}
    editors_list = []

    current = week_start
    while current <= week_end:
        date_str = current.strftime("%Y-%m-%d")
        day_data = fetch_summary(date_str)
        if day_data:
            total_seconds += day_data.get("total_seconds", 0)
            total_ai_in += day_data.get("ai_input_tokens", 0)
            total_ai_out += day_data.get("ai_output_tokens", 0)
            total_prompts += day_data.get("ai_prompts", 0)

            # Categories aggregation
            for cat in day_data.get("categories", []):
                name = cat["name"]
                if name not in categories_agg:
                    categories_agg[name] = 0
                categories_agg[name] += cat.get("total_seconds", 0)

            # Editors (take from last day for simplicity, or aggregate)
            for ed in day_data.get("editors", []):
                total_additions += ed.get("ai_additions", 0)
                total_deletions += ed.get("ai_deletions", 0)

        current += timedelta(days=1)

    # Format categories
    categories = []
    for name, seconds in sorted(categories_agg.items(), key=lambda x: -x[1]):
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        text = f"{hours}h {mins:02d}m" if hours > 0 else f"{mins}m"
        categories.append({"name": name, "text": text})

    # Coding time
    hours = int(total_seconds // 3600)
    mins = int((total_seconds % 3600) // 60)
    coding_time = f"{hours}h {mins:02d}m"

    # AI driven percentage (simplified: 100% if additions > 0)
    ai_driven_pct = 100 if total_additions > 0 else 0
    ai_additions = fmt_additions(total_additions)
    human_additions = "0"
    line_changes = fmt_additions(total_additions + total_deletions)

    cost = "$0"
    prompts = str(total_prompts)
    tokens_total = fmt_tokens(total_ai_in + total_ai_out)
    tokens_in = fmt_tokens(total_ai_in)
    tokens_out = fmt_tokens(total_ai_out)
    human_followup = "0%"

    html = render_dashboard(
        date_range=date_range,
        ai_driven_pct=ai_driven_pct,
        ai_additions=ai_additions,
        human_additions=human_additions,
        line_changes=line_changes,
        cost=cost,
        prompts=prompts,
        tokens_total=tokens_total,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        human_followup=human_followup,
        coding_time=coding_time,
        categories=categories,
    )

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, f"ai-overview-{end_str}.html")
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
