"""Hermes state.db queries for daily report generation."""

import sqlite3
import os
from datetime import datetime, timezone, timedelta
from collections import Counter
from typing import List, Dict, Any, Tuple

DB_PATH = os.path.expanduser("~/.hermes/state.db")
MELBOURNE_TZ = timezone(timedelta(hours=10))


def get_yesterday_range() -> Tuple[datetime, datetime, datetime]:
    """Return (start_dt, end_dt, yesterday_dt) in UTC (matches Dashboard)."""
    now_utc = datetime.now(timezone.utc)
    yesterday = now_utc - timedelta(days=1)
    start = datetime(yesterday.year, yesterday.month, yesterday.day, 0, 0, 0, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    return start, end, yesterday


def fetch_sessions(start_ts: float, end_ts: float) -> List[sqlite3.Row]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT id, source, model, started_at, ended_at, message_count, tool_call_count,
               input_tokens, output_tokens, cache_read_tokens, cache_write_tokens,
               reasoning_tokens, title
        FROM sessions
        WHERE started_at >= ? AND started_at < ?
        ORDER BY started_at DESC
    """, (start_ts, end_ts))
    rows = cur.fetchall()
    conn.close()
    return rows


def fetch_tool_calls(session_id: str) -> Counter:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT tool_calls FROM messages
        WHERE session_id = ? AND role = 'assistant' AND tool_calls IS NOT NULL
    """, (session_id,))
    counter = Counter()
    for row in cur.fetchall():
        name = _extract_tool_name(row['tool_calls'])
        if name:
            counter[name] += 1
    conn.close()
    return counter


def _extract_tool_name(tool_call_json) -> str:
    import json
    try:
        calls = json.loads(tool_call_json) if isinstance(tool_call_json, str) else tool_call_json
        if calls and len(calls) > 0:
            call_id = calls[0].get("id", "")
            return call_id.split(":")[0] if ":" in call_id else call_id
    except Exception:
        pass
    return ""


def aggregate_stats(sessions: List[sqlite3.Row]) -> Dict[str, Any]:
    return {
        "total_input": sum(s['input_tokens'] or 0 for s in sessions),
        "total_output": sum(s['output_tokens'] or 0 for s in sessions),
        "total_cache_read": sum(s['cache_read_tokens'] or 0 for s in sessions),
        "total_cache_write": sum(s['cache_write_tokens'] or 0 for s in sessions),
        "total_reasoning": sum(s['reasoning_tokens'] or 0 for s in sessions),
        "total_msgs": sum(s['message_count'] or 0 for s in sessions),
        "total_tools": sum(s['tool_call_count'] or 0 for s in sessions),
        "session_count": len(sessions),
    }


def fetch_all_sessions() -> List[sqlite3.Row]:
    """Fetch all historical sessions from state.db."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT id, source, model, started_at, ended_at, message_count, tool_call_count,
               input_tokens, output_tokens, cache_read_tokens, cache_write_tokens,
               reasoning_tokens, title
        FROM sessions
        ORDER BY started_at DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def aggregate_all_time() -> Dict[str, Any]:
    """Aggregate all-time stats from state.db."""
    sessions = fetch_all_sessions()
    models = Counter()
    sources = Counter()
    all_tools = Counter()

    for s in sessions:
        if s['model']:
            models[s['model']] += 1
        if s['source']:
            sources[s['source']] += 1
        # Count tool calls per session
        tools = fetch_tool_calls(s['id'])
        all_tools.update(tools)

    stats = aggregate_stats(sessions)
    stats['models'] = models
    stats['sources'] = sources
    stats['top_tools'] = all_tools.most_common(10)
    stats['sessions'] = sessions
    return stats
