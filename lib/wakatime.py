"""WakaTime API client — fetch daily coding summaries."""

import base64
import os
import requests
from typing import Optional, Dict, Any

API_KEY = os.environ.get("WAKATIME_API_KEY", "")
BASE_URL = "https://wakatime.com/api/v1"


def fetch_summary(date_str: str) -> Optional[Dict[str, Any]]:
    """Fetch WakaTime summary for a single date (YYYY-MM-DD)."""
    if not API_KEY:
        print("WAKATIME_API_KEY not set")
        return None
    try:
        auth = base64.b64encode(API_KEY.encode()).decode()
        url = f"{BASE_URL}/users/current/summaries?start={date_str}&end={date_str}"
        resp = requests.get(url, headers={"Authorization": f"Basic {auth}"}, timeout=10)
        if resp.status_code == 200:
            data = resp.json().get("data", [])
            if data:
                day = data[0]
                total = day.get("grand_total", {})
                return {
                    "total_seconds": total.get("total_seconds", 0),
                    "total_text": total.get("text", "0 mins"),
                    "categories": day.get("categories", []),
                    "editors": day.get("editors", []),
                    "ai_input_tokens": total.get("ai_input_tokens", 0) or day.get("ai_input_tokens", 0),
                    "ai_output_tokens": total.get("ai_output_tokens", 0) or day.get("ai_output_tokens", 0),
                    "ai_prompts": total.get("ai_prompt_events", 0) or day.get("ai_prompt_events", 0),
                    "ai_additions": total.get("ai_additions", 0),
                    "ai_deletions": total.get("ai_deletions", 0),
                }
    except Exception as e:
        print(f"WakaTime error: {e}")
    return None
