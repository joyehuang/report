"""Local cache for WakaTime daily data (free tier = 7 day history)."""

import json
import os

HISTORY_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "wakatime_history.json"
)


def _load() -> dict:
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save(data: dict):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def merge_day(date_str: str, day_data: dict):
    """Merge a single day's WakaTime data into history."""
    if not day_data:
        return
    data = _load()
    data[date_str] = {
        "total_seconds": day_data.get("total_seconds", 0),
        "ai_input_tokens": day_data.get("ai_input_tokens", 0),
        "ai_output_tokens": day_data.get("ai_output_tokens", 0),
        "ai_prompts": day_data.get("ai_prompts", 0),
        "ai_additions": day_data.get("ai_additions", 0),
        "ai_deletions": day_data.get("ai_deletions", 0),
        "categories": day_data.get("categories", []),
        "editors": day_data.get("editors", []),
    }
    _save(data)


def get_cumulative() -> dict:
    """Return cumulative stats from all historical data."""
    data = _load()
    total_seconds = 0
    total_ai_in = 0
    total_ai_out = 0
    total_prompts = 0
    total_additions = 0
    total_deletions = 0
    categories_agg = {}

    for date_str, day in data.items():
        total_seconds += day.get("total_seconds", 0)
        total_ai_in += day.get("ai_input_tokens", 0)
        total_ai_out += day.get("ai_output_tokens", 0)
        total_prompts += day.get("ai_prompts", 0)
        total_additions += day.get("ai_additions", 0)
        total_deletions += day.get("ai_deletions", 0)

        for cat in day.get("categories", []):
            name = cat["name"]
            categories_agg[name] = categories_agg.get(name, 0) + cat.get("total_seconds", 0)

    return {
        "total_seconds": total_seconds,
        "total_ai_in": total_ai_in,
        "total_ai_out": total_ai_out,
        "total_prompts": total_prompts,
        "total_additions": total_additions,
        "total_deletions": total_deletions,
        "categories": categories_agg,
        "days_recorded": len(data),
        "date_range": _get_date_range(data),
    }


def _get_date_range(data: dict) -> str:
    if not data:
        return ""
    dates = sorted(data.keys())
    return f"{dates[0]} ~ {dates[-1]}"
