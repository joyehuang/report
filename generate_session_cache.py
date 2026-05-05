#!/usr/bin/env python3
"""Generate session-level cache analysis dashboard at archive/session-cache.html."""

import os
import sys
import json
import sqlite3
import html as html_lib
from datetime import datetime, timezone, timedelta

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "archive")
DB_PATH = os.path.expanduser("~/.hermes/state.db")
MELBOURNE_TZ = timezone(timedelta(hours=10))


def fmt_tokens(n):
    n = n or 0
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def fmt_dt(ts):
    if ts is None:
        return "—"
    dt = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(MELBOURNE_TZ)
    return dt.strftime("%Y-%m-%d %H:%M")


def ratio_class(r):
    if r >= 80:
        return "ratio-good"
    if r >= 50:
        return "ratio-mid"
    return "ratio-bad"


def fetch_sessions():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT id, model, started_at,
               input_tokens, output_tokens,
               cache_read_tokens, cache_write_tokens,
               message_count, tool_call_count, title
        FROM sessions
        ORDER BY started_at DESC
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def generate():
    sessions = fetch_sessions()

    # Per-session computed fields
    for s in sessions:
        inp = s["input_tokens"] or 0
        cr = s["cache_read_tokens"] or 0
        denom = inp + cr
        s["hit_ratio"] = (cr / denom * 100) if denom > 0 else 0.0

    # Overall stats
    total_sessions = len(sessions)
    total_cache_read = sum((s["cache_read_tokens"] or 0) for s in sessions)
    total_cache_write = sum((s["cache_write_tokens"] or 0) for s in sessions)
    total_input = sum((s["input_tokens"] or 0) for s in sessions)
    total_prompt = total_input + total_cache_read
    overall_ratio = (total_cache_read / total_prompt * 100) if total_prompt > 0 else 0.0
    avg_hit_ratio = (
        sum(s["hit_ratio"] for s in sessions) / total_sessions if total_sessions else 0.0
    )

    # Models for filtering
    models = sorted({(s["model"] or "unknown") for s in sessions})

    # Filter buttons
    filter_buttons = '<button class="filter-btn active" data-model="all">All</button>'
    for m in models:
        filter_buttons += (
            f'<button class="filter-btn" data-model="{html_lib.escape(m)}">'
            f'{html_lib.escape(m)}</button>'
        )

    # Build table rows
    table_rows = ""
    for s in sessions:
        model = s["model"] or "unknown"
        rc = ratio_class(s["hit_ratio"])
        title = s.get("title") or s["id"]
        title_attr = html_lib.escape(str(title))
        table_rows += f"""      <tr data-model="{html_lib.escape(model)}" title="{title_attr}">
        <td>{fmt_dt(s['started_at'])}</td>
        <td><code>{html_lib.escape(model)}</code></td>
        <td>{fmt_tokens(s['input_tokens'])}</td>
        <td>{fmt_tokens(s['cache_read_tokens'])}</td>
        <td>{fmt_tokens(s['cache_write_tokens'])}</td>
        <td>{fmt_tokens(s['output_tokens'])}</td>
        <td><span class="ratio {rc}">{s['hit_ratio']:.1f}%</span></td>
        <td>{s['message_count'] or 0}</td>
      </tr>
"""

    html = f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Session Cache Analysis — joyehuang.me</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: hsl(210 33% 99%);
    --card: hsl(0 0% 100%);
    --border: hsl(240 5.9% 88%);
    --text: hsl(240 10% 3.9%);
    --text-dim: hsl(240 3.8% 46.1%);
    --text-muted: hsl(240 3.8% 60%);
    --accent: hsl(200 29% 45%);
    --accent-soft: hsl(200 70% 90%);
    --green: hsl(142 60% 40%);
    --yellow: hsl(38 92% 45%);
    --red: hsl(0 72% 50%);
    --toggle-bg: hsl(240 4.8% 95.9%);
    --toggle-icon: hsl(240 10% 3.9%);
  }}
  [data-theme="dark"] {{
    --bg: hsl(240 20.54% 5.2%);
    --card: hsl(240 10% 3.9%);
    --border: hsl(240 3.7% 15.9%);
    --text: hsl(0 0% 98%);
    --text-dim: hsl(240 5% 74.9%);
    --text-muted: hsl(240 5% 50%);
    --accent: hsl(195 95% 85%);
    --accent-soft: hsl(195 70% 20%);
    --green: hsl(142 60% 65%);
    --yellow: hsl(48 95% 65%);
    --red: hsl(0 80% 70%);
    --toggle-bg: hsl(240 3.7% 15.9%);
    --toggle-icon: hsl(0 0% 98%);
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Inter', system-ui, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    min-height: 100vh;
    -webkit-font-smoothing: antialiased;
  }}
  .page {{ max-width: 1100px; margin: 0 auto; padding: 40px 24px; }}

  .top-bar {{
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 32px;
  }}
  .brand {{
    font-family: 'JetBrains Mono', monospace; font-size: 11px;
    color: var(--text-dim); letter-spacing: 3px; text-transform: uppercase;
  }}
  .brand a {{ color: inherit; text-decoration: none; }}
  .brand a:hover {{ color: var(--accent); }}

  .theme-toggle {{
    width: 40px; height: 40px; border-radius: 10px;
    border: 1px solid var(--border); background: var(--toggle-bg);
    color: var(--toggle-icon); cursor: pointer;
    display: grid; place-items: center; transition: all 0.2s ease;
  }}
  .theme-toggle:hover {{ transform: scale(1.05); border-color: var(--accent); }}
  .theme-toggle svg {{
    width: 18px; height: 18px; stroke: currentColor; stroke-width: 2;
    fill: none; stroke-linecap: round; stroke-linejoin: round;
  }}
  .theme-toggle .sun, [data-theme="light"] .theme-toggle .moon {{ display: none; }}
  [data-theme="light"] .theme-toggle .sun {{ display: block; }}

  .header {{ margin-bottom: 32px; }}
  .header h1 {{ font-size: 36px; font-weight: 700; letter-spacing: -1px; }}
  .header h1 span {{ color: var(--accent); }}
  .header .meta {{
    font-size: 13px; color: var(--text-dim); margin-top: 8px;
  }}

  .hero {{
    background: var(--card); border: 1px solid var(--border);
    border-radius: 12px; padding: 40px 24px; text-align: center; margin-bottom: 24px;
  }}
  .hero .big {{
    font-family: 'JetBrains Mono', monospace; font-size: 56px;
    font-weight: 700; color: var(--green);
  }}
  .hero .lbl {{
    font-size: 13px; color: var(--text-dim);
    text-transform: uppercase; letter-spacing: 2px; margin-top: 8px;
  }}
  .hero .sub {{
    font-size: 12px; color: var(--text-muted); margin-top: 8px;
  }}

  .grid-3 {{
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 24px;
  }}
  .mini-card {{
    background: var(--card); border: 1px solid var(--border);
    border-radius: 10px; padding: 20px; text-align: center;
  }}
  .mini-card .num {{
    font-family: 'JetBrains Mono', monospace; font-size: 22px;
    font-weight: 700; color: var(--text);
  }}
  .mini-card .lbl {{
    font-size: 11px; color: var(--text-dim);
    text-transform: uppercase; letter-spacing: 1px; margin-top: 4px;
  }}

  .section {{
    background: var(--card); border: 1px solid var(--border);
    border-radius: 12px; padding: 24px; margin-bottom: 16px;
  }}
  .section-title {{
    font-size: 14px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 2px; color: var(--text-dim); margin-bottom: 16px;
  }}

  .filter-bar {{
    display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px;
  }}
  .filter-btn {{
    font-family: 'JetBrains Mono', monospace; font-size: 12px;
    padding: 6px 12px; border-radius: 6px;
    border: 1px solid var(--border); background: var(--card);
    color: var(--text-dim); cursor: pointer; transition: all 0.15s ease;
  }}
  .filter-btn:hover {{ color: var(--text); border-color: var(--accent); }}
  .filter-btn.active {{
    background: var(--accent-soft); color: var(--text);
    border-color: var(--accent);
  }}

  .table-wrap {{ overflow-x: auto; }}
  .data-table {{
    width: 100%; border-collapse: collapse; font-size: 13px;
  }}
  .data-table th, .data-table td {{
    text-align: left; padding: 10px 12px;
    border-bottom: 1px solid var(--border); white-space: nowrap;
  }}
  .data-table th {{
    font-size: 11px; text-transform: uppercase; letter-spacing: 1px;
    color: var(--text-dim); font-weight: 600;
  }}
  .data-table td {{ color: var(--text); }}
  .data-table tr:hover td {{ background: var(--accent-soft); }}
  .data-table code {{
    font-family: 'JetBrains Mono', monospace; font-size: 12px;
    background: var(--border); padding: 2px 6px; border-radius: 4px;
  }}
  .ratio {{
    font-family: 'JetBrains Mono', monospace; font-weight: 600;
  }}
  .ratio-good {{ color: var(--green); }}
  .ratio-mid {{ color: var(--yellow); }}
  .ratio-bad {{ color: var(--red); }}

  .empty {{
    text-align: center; color: var(--text-muted);
    font-size: 13px; padding: 24px;
  }}

  .footer {{
    margin-top: 40px; padding-top: 20px;
    border-top: 1px solid var(--border); text-align: center;
  }}
  .footer a {{
    color: var(--text-dim); text-decoration: none; font-size: 12px;
    transition: color 0.2s;
  }}
  .footer a:hover {{ color: var(--accent); }}

  @media (max-width: 640px) {{
    .page {{ padding: 24px 16px; }}
    .header h1 {{ font-size: 28px; }}
    .hero .big {{ font-size: 40px; }}
    .grid-3 {{ grid-template-columns: 1fr; }}
    .data-table {{ font-size: 11px; }}
    .data-table th, .data-table td {{ padding: 8px 6px; }}
  }}
</style>
</head>
<body>

<div class="page">
  <div class="top-bar">
    <div class="brand"><a href="../index.html">← AI Usage Report</a></div>
    <button class="theme-toggle" id="themeToggle" aria-label="Toggle theme">
      <svg class="moon" viewBox="0 0 24 24"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
      <svg class="sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="5"/><path d="M12 1v2"/><path d="M12 21v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M1 12h2"/><path d="M21 12h2"/><path d="m4.93 19.07 1.41-1.41"/><path d="m17.66 6.34 1.41-1.41"/></svg>
    </button>
  </div>

  <div class="header">
    <h1>Session <span>Cache</span></h1>
    <p class="meta">Per-session prompt cache hit ratio across all Hermes sessions</p>
  </div>

  <div class="hero">
    <div class="big">{avg_hit_ratio:.1f}%</div>
    <div class="lbl">Average Session Hit Ratio</div>
    <div class="sub">overall: {overall_ratio:.1f}% · {fmt_tokens(total_cache_read)} cached / {fmt_tokens(total_prompt)} prompt tokens</div>
  </div>

  <div class="grid-3">
    <div class="mini-card">
      <div class="num">{total_sessions}</div>
      <div class="lbl">Total Sessions</div>
    </div>
    <div class="mini-card">
      <div class="num">{fmt_tokens(total_cache_read)}</div>
      <div class="lbl">Total Cache Read</div>
    </div>
    <div class="mini-card">
      <div class="num">{fmt_tokens(total_cache_write)}</div>
      <div class="lbl">Total Cache Write</div>
    </div>
  </div>

  <div class="section">
    <div class="section-title">Sessions</div>
    <div class="filter-bar">{filter_buttons}</div>
    <div class="table-wrap">
      <table class="data-table" id="sessionsTable">
        <thead>
          <tr>
            <th>Started (Melb)</th>
            <th>Model</th>
            <th>Input</th>
            <th>Cache Read</th>
            <th>Cache Write</th>
            <th>Output</th>
            <th>Hit Ratio</th>
            <th>Msgs</th>
          </tr>
        </thead>
        <tbody id="sessionsBody">
{table_rows}        </tbody>
      </table>
      <div class="empty" id="emptyMsg" style="display:none">No sessions match this filter.</div>
    </div>
  </div>

  <div class="footer">
    <a href="https://joyehuang.me" target="_blank">joyehuang.me</a> ·
    <a href="https://github.com/joyehuang" target="_blank">GitHub</a> ·
    <a href="https://github.com/joyehuang/report" target="_blank">Source</a>
  </div>
</div>

<script>
(function() {{
  const html = document.documentElement;
  const toggle = document.getElementById('themeToggle');
  const saved = localStorage.getItem('theme');
  if (saved) html.dataset.theme = saved;
  toggle.addEventListener('click', () => {{
    const next = html.dataset.theme === 'dark' ? 'light' : 'dark';
    html.dataset.theme = next;
    localStorage.setItem('theme', next);
  }});

  const buttons = document.querySelectorAll('.filter-btn');
  const rows = document.querySelectorAll('#sessionsBody tr');
  const emptyMsg = document.getElementById('emptyMsg');
  buttons.forEach(btn => {{
    btn.addEventListener('click', () => {{
      buttons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const m = btn.dataset.model;
      let visible = 0;
      rows.forEach(r => {{
        const show = m === 'all' || r.dataset.model === m;
        r.style.display = show ? '' : 'none';
        if (show) visible++;
      }});
      emptyMsg.style.display = visible === 0 ? 'block' : 'none';
    }});
  }});
}})();
</script>

</body>
</html>"""

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, "session-cache.html")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Session cache analysis saved: {filepath}")
    return filepath


if __name__ == "__main__":
    path = generate()
    print(f"OK: {path}")
