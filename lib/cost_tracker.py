"""Manual cost tracking for AI usage bills."""

import json
import os
import time
from typing import Optional

COSTS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "costs.json")


def _load() -> dict:
    if os.path.exists(COSTS_FILE):
        with open(COSTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}
    data.setdefault("bills", [])
    data.setdefault("services", [])
    # Migrate legacy total_usd → total_ai_usd
    if "total_ai_usd" not in data:
        data["total_ai_usd"] = data.pop("total_usd", 0.0)
    data.setdefault("total_services_usd", 0.0)
    return data


def _save(data: dict):
    os.makedirs(os.path.dirname(COSTS_FILE), exist_ok=True)
    with open(COSTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def parse_date(date_str: str) -> str:
    """Normalize yymmdd to YYYY-MM-DD."""
    if len(date_str) == 6 and date_str.isdigit():
        return f"20{date_str[:2]}-{date_str[2:4]}-{date_str[4:]}"
    return date_str


def add_bill(date: str, provider: str, cost: float, currency: str = "USD", note: str = "") -> dict:
    """Add a daily bill with original currency + USD normalization.
    
    Args:
        date: yymmdd format (e.g., "260503" for 2026-05-03)
        provider: e.g., "kimi", "openai", "anthropic"
        cost: cost in original currency
        currency: "USD", "CNY", "AUD"
        note: optional note
    """
    # Exchange rates (approximate, user can adjust)
    rates = {"USD": 1.0, "CNY": 0.1478, "AUD": 0.7178}
    rate = rates.get(currency.upper(), 1.0)
    cost_usd = round(cost * rate, 2)

    data = _load()
    date_norm = parse_date(date)
    entry = {
        "date": date_norm,
        "date_raw": date,
        "provider": provider.lower().strip(),
        "cost_original": round(cost, 2),
        "currency": currency.upper(),
        "cost_usd": cost_usd,
        "note": note,
        "added_at": int(time.time()),
    }
    data["bills"].append(entry)
    data["bills"].sort(key=lambda x: x["date"])
    data["total_ai_usd"] = round(sum(b["cost_usd"] for b in data["bills"]), 2)
    _save(data)
    return entry


def add_service_cost(service: str, cost_usd: float, month: str, note: str = "") -> dict:
    """Add a non-AI infrastructure service cost entry.

    Args:
        service: e.g., "aws", "vercel", "cloudflare", "typeless"
        cost_usd: cost in USD
        month: YYYY-MM
        note: optional note
    """
    data = _load()
    entry = {
        "service": service.lower().strip(),
        "cost_usd": round(cost_usd, 2),
        "month": month,
        "note": note,
        "added_at": int(time.time()),
    }
    data["services"].append(entry)
    data["services"].sort(key=lambda x: (x["month"], x["service"]))
    data["total_services_usd"] = round(sum(s["cost_usd"] for s in data["services"]), 2)
    _save(data)
    return entry


def get_summary() -> dict:
    """Return combined AI + service cost summary."""
    data = _load()

    # AI costs (from bills)
    ai_by_month = {}
    ai_by_provider = {}
    for b in data["bills"]:
        month = b["date"][:7]  # YYYY-MM
        ai_by_month.setdefault(month, {"cost_usd": 0.0, "entries": []})
        ai_by_month[month]["cost_usd"] += b["cost_usd"]
        ai_by_month[month]["entries"].append(b)

        ai_by_provider.setdefault(b["provider"], {"cost_usd": 0.0, "count": 0})
        ai_by_provider[b["provider"]]["cost_usd"] += b["cost_usd"]
        ai_by_provider[b["provider"]]["count"] += 1

    # Service costs
    svc_by_month = {}
    svc_by_service = {}
    for s in data["services"]:
        month = s["month"]
        svc_by_month.setdefault(month, {"cost_usd": 0.0, "entries": []})
        svc_by_month[month]["cost_usd"] += s["cost_usd"]
        svc_by_month[month]["entries"].append(s)

        svc_by_service.setdefault(s["service"], {"cost_usd": 0.0, "entries": []})
        svc_by_service[s["service"]]["cost_usd"] += s["cost_usd"]
        svc_by_service[s["service"]]["entries"].append(s)

    ai_total = data["total_ai_usd"]
    svc_total = data["total_services_usd"]

    return {
        "ai": {
            "total_usd": ai_total,
            "bills": data["bills"],
            "by_month": {k: {"cost_usd": round(v["cost_usd"], 2), "entries": v["entries"]} for k, v in ai_by_month.items()},
            "by_provider": {k: {"cost_usd": round(v["cost_usd"], 2), "count": v["count"]} for k, v in ai_by_provider.items()},
        },
        "services": {
            "total_usd": svc_total,
            "entries": data["services"],
            "by_month": {k: {"cost_usd": round(v["cost_usd"], 2), "entries": v["entries"]} for k, v in svc_by_month.items()},
            "by_service": {k: {"cost_usd": round(v["cost_usd"], 2), "entries": v["entries"]} for k, v in svc_by_service.items()},
        },
        "combined_total": round(ai_total + svc_total, 2),
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
