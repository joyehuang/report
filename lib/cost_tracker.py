"""Manual cost tracking for AI usage bills."""

import json
import os
import time
from typing import Optional

COSTS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "costs.json")


def _load() -> dict:
    if os.path.exists(COSTS_FILE):
        with open(COSTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"bills": [], "total_usd": 0.0}


def _save(data: dict):
    os.makedirs(os.path.dirname(COSTS_FILE), exist_ok=True)
    with open(COSTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def parse_date(date_str: str) -> str:
    """Normalize yymmdd to YYYY-MM-DD."""
    if len(date_str) == 6 and date_str.isdigit():
        return f"20{date_str[:2]}-{date_str[2:4]}-{date_str[4:]}"
    return date_str


def add_bill(date: str, provider: str, cost_usd: float, note: str = "") -> dict:
    """Add a daily bill.
    
    Args:
        date: yymmdd format (e.g., "260503" for 2026-05-03)
        provider: e.g., "kimi", "openai", "anthropic"
        cost_usd: cost in USD
        note: optional note
    """
    data = _load()
    date_norm = parse_date(date)
    entry = {
        "date": date_norm,
        "date_raw": date,
        "provider": provider.lower().strip(),
        "cost_usd": round(cost_usd, 2),
        "note": note,
        "added_at": int(time.time()),
    }
    # Append — no dedup; user may have multiple charges same day
    data["bills"].append(entry)
    data["bills"].sort(key=lambda x: x["date"])
    data["total_usd"] = round(sum(b["cost_usd"] for b in data["bills"]), 2)
    _save(data)
    return entry


def get_summary() -> dict:
    """Return cost summary grouped by month and provider."""
    data = _load()
    by_month = {}
    by_provider = {}
    for b in data["bills"]:
        month = b["date"][:7]  # YYYY-MM
        by_month.setdefault(month, {"cost_usd": 0.0, "entries": []})
        by_month[month]["cost_usd"] += b["cost_usd"]
        by_month[month]["entries"].append(b)
        
        by_provider.setdefault(b["provider"], {"cost_usd": 0.0, "count": 0})
        by_provider[b["provider"]]["cost_usd"] += b["cost_usd"]
        by_provider[b["provider"]]["count"] += 1
    return {
        "total_usd": data["total_usd"],
        "bills": data["bills"],
        "by_month": {k: {"cost_usd": round(v["cost_usd"], 2), "entries": v["entries"]} for k, v in by_month.items()},
        "by_provider": {k: {"cost_usd": round(v["cost_usd"], 2), "count": v["count"]} for k, v in by_provider.items()},
    }


def get_cost_for_month(month: str) -> float:
    """Get total cost for a specific month (YYYY-MM)."""
    data = _load()
    return round(sum(b["cost_usd"] for b in data["bills"] if b["date"].startswith(month)), 2)


def get_cost_for_date_range(start_date: str, end_date: str) -> float:
    """Get total cost for a date range (YYYY-MM-DD format)."""
    data = _load()
    return round(sum(
        b["cost_usd"] for b in data["bills"]
        if start_date <= b["date"] <= end_date
    ), 2)
