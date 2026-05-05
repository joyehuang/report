#!/usr/bin/env python3
"""Generate index.html dynamically from actual report files."""

import os
import re
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARCHIVE_DIR = os.path.join(BASE_DIR, "archive")


def fmt_big(n):
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def fmt_duration(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    return f"{h}h {m:02d}m"


def find_latest_receipt():
    """Find the latest receipt HTML file and extract key metrics."""
    files = [f for f in os.listdir(ARCHIVE_DIR) if f.startswith("joye-receipt-") and f.endswith(".html")]
    if not files:
        return None
    files.sort(reverse=True)
    latest = files[0]
    filepath = os.path.join(ARCHIVE_DIR, latest)

    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()

    # Extract metrics from the token-grid or token usage section
    # Try to find: Sessions big number, grid numbers
    session_match = re.search(r'<div class="big-number">(\d+)</div>', html)
    sessions = session_match.group(1) if session_match else "0"

    # Grid values: messages, tool calls, total tokens
    grid_matches = re.findall(r'<div class="num">([0-9.KM]+)</div>', html)
    msgs = grid_matches[0] if len(grid_matches) > 0 else "0"
    tools = grid_matches[1] if len(grid_matches) > 1 else "0"
    tokens = grid_matches[2] if len(grid_matches) > 2 else "0"

    # Date from filename: joye-receipt-2026-05-03.html
    date_str = latest.replace("joye-receipt-", "").replace(".html", "")
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        display_date = dt.strftime("%B %-d, %Y")
        short_date = dt.strftime("%Y-%m-%d")
    except ValueError:
        display_date = date_str
        short_date = date_str

    return {
        "filename": latest,
        "href": f"archive/{latest}",
        "date_str": date_str,
        "display_date": display_date,
        "short_date": short_date,
        "sessions": sessions,
        "messages": msgs,
        "tool_calls": tools,
        "tokens": tokens,
    }


def find_latest_dashboard():
    """Find the latest AI Overview dashboard summary JSON."""
    files = [f for f in os.listdir(ARCHIVE_DIR) if f.startswith("ai-overview-") and f.endswith(".json")]
    if not files:
        return None
    files.sort(reverse=True)
    latest = files[0]
    filepath = os.path.join(ARCHIVE_DIR, latest)

    import json
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Date from filename
    date_str = latest.replace("ai-overview-", "").replace(".json", "")

    return {
        "filename": latest.replace(".json", ".html"),
        "href": f"archive/{latest.replace('.json', '.html')}",
        "date_str": date_str,
        "week_range": data.get("date_range", ""),
        "coding_time": data.get("coding_time", "0h"),
        "ai_in": data.get("ai_in", "0"),
        "prompts": data.get("prompts", "0"),
        "sessions": "—",  # WakaTime doesn't track sessions count directly
    }


def get_archive_list():
    """List all receipt files for the archive section."""
    files = [f for f in os.listdir(ARCHIVE_DIR) if f.startswith("joye-receipt-") and f.endswith(".html")]
    files.sort(reverse=True)
    items = []
    for f in files[:30]:
        date_str = f.replace("joye-receipt-", "").replace(".html", "")
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            display = dt.strftime("%B %-d")
        except ValueError:
            display = date_str

        # Extract tokens and sessions from the file
        filepath = os.path.join(ARCHIVE_DIR, f)
        with open(filepath, "r", encoding="utf-8") as fh:
            html = fh.read()
        session_match = re.search(r'<div class="big-number">(\d+)</div>', html)
        sess = session_match.group(1) if session_match else "?"
        grid_matches = re.findall(r'<div class="num">([0-9.KM]+)</div>', html)
        toks = grid_matches[2] if len(grid_matches) > 2 else "?"

        items.append({
            "href": f"archive/{f}",
            "date": date_str,
            "title": f"Daily Receipt — {display}",
            "meta": f"{sess} sessions · {toks} tokens",
        })
    return items


def get_dashboard_archive_list():
    """List all AI Overview dashboard files for the archive section."""
    files = [f for f in os.listdir(ARCHIVE_DIR) if f.startswith("ai-overview-") and f.endswith(".json")]
    files.sort(reverse=True)
    items = []
    import json
    for f in files[:20]:
        date_str = f.replace("ai-overview-", "").replace(".json", "")
        filepath = os.path.join(ARCHIVE_DIR, f)
        try:
            with open(filepath, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            continue
        week_range = data.get("date_range", date_str)
        coding_time = data.get("coding_time", "")
        tokens_total = data.get("tokens_total", "")
        items.append({
            "href": f"archive/{f.replace('.json', '.html')}",
            "date": date_str,
            "title": f"AI Overview — {week_range}",
            "meta": f"{coding_time} · {tokens_total} tokens",
        })
    return items


def generate():
    # First regenerate the overview page
    try:
        import generate_overview
        generate_overview.generate()
    except Exception as e:
        print(f"overview.html generation skipped: {e}")

    receipt = find_latest_receipt()
    dashboard = find_latest_dashboard()
    archive_items = get_archive_list()

    # Build overview card data
    try:
        from lib.wakatime_history import get_cumulative
        from lib.cost_tracker import get_summary
        from lib.hermes_db import aggregate_all_time
        waka = get_cumulative()
        cost = get_summary()
        hermes = aggregate_all_time()
        hermes_tokens = hermes.get("total_input", 0) + hermes.get("total_output", 0)
        waka_tokens = waka.get("total_ai_in", 0) + waka.get("total_ai_out", 0)
        grand_tokens = hermes_tokens + waka_tokens
        overview_card = f"""    <a class="featured-card" href="archive/overview.html">
      <div class="date">Cumulative Overview</div>
      <div class="title">AI Usage Overview</div>
      <div class="featured-stats">
        <div class="stat">
          <div class="num">${cost['total_usd']:.0f}</div>
          <div class="lbl">Cost</div>
        </div>
        <div class="stat">
          <div class="num">{fmt_big(grand_tokens)}</div>
          <div class="lbl">Tokens</div>
        </div>
        <div class="stat">
          <div class="num">{fmt_duration(waka.get('total_seconds', 0))}</div>
          <div class="lbl">Coding</div>
        </div>
        <div class="stat">
          <div class="num">{fmt_big(waka.get('total_prompts', 0))}</div>
          <div class="lbl">Prompts</div>
        </div>
      </div>
    </a>"""
    except Exception as e:
        overview_card = f'<div class="featured-card"><div class="title">Overview — {e}</div></div>'

    # Build receipt card
    if receipt:
        receipt_card = f"""    <a class="featured-card" href="{receipt['href']}">
      <div class="date">{receipt['display_date']}</div>
      <div class="title">Hermes Agent Daily Receipt — {receipt['short_date']}</div>
      <div class="featured-stats">
        <div class="stat">
          <div class="num">{receipt['sessions']}</div>
          <div class="lbl">Sessions</div>
        </div>
        <div class="stat">
          <div class="num">{receipt['tokens']}</div>
          <div class="lbl">Tokens</div>
        </div>
        <div class="stat">
          <div class="num">{receipt['messages']}</div>
          <div class="lbl">Messages</div>
        </div>
        <div class="stat">
          <div class="num">{receipt['tool_calls']}</div>
          <div class="lbl">Tool Calls</div>
        </div>
      </div>
    </a>"""
    else:
        receipt_card = '<div class="featured-card"><div class="title">No receipts yet</div></div>'

    # Build dashboard card
    if dashboard:
        dashboard_card = f"""    <a class="featured-card" href="{dashboard['href']}">
      <div class="date">{dashboard['week_range'] or 'Weekly Overview'}</div>
      <div class="title">AI Overview Dashboard</div>
      <div class="featured-stats">
        <div class="stat">
          <div class="num">{dashboard['coding_time']}</div>
          <div class="lbl">Coding</div>
        </div>
        <div class="stat">
          <div class="num">{dashboard['ai_in']}</div>
          <div class="lbl">AI In</div>
        </div>
        <div class="stat">
          <div class="num">{dashboard['prompts']}</div>
          <div class="lbl">Prompts</div>
        </div>
        <div class="stat">
          <div class="num">{dashboard['sessions']}</div>
          <div class="lbl">Sessions</div>
        </div>
      </div>
    </a>"""
    else:
        dashboard_card = '<div class="featured-card"><div class="title">AI Overview — no data</div></div>'

    # Build archive grids
    archive_items = get_archive_list()
    archive_grid = ""
    for item in archive_items:
        archive_grid += f"""      <a class="archive-item" href="{item['href']}">
        <div class="arc-date">{item['date']}</div>
        <div class="arc-title">{item['title']}</div>
        <div class="arc-meta">
          <span>{item['meta']}</span>
        </div>
      </a>
"""

    dashboard_archive_items = get_dashboard_archive_list()
    dashboard_archive_grid = ""
    for item in dashboard_archive_items:
        dashboard_archive_grid += f"""      <a class="archive-item" href="{item['href']}">
        <div class="arc-date">{item['date']}</div>
        <div class="arc-title">{item['title']}</div>
        <div class="arc-meta">
          <span>{item['meta']}</span>
        </div>
      </a>
"""

    html = f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Usage Report — joyehuang.me</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: hsl(210 33% 99%);
    --bg-card: hsl(0 0% 100%);
    --bg-card-hover: hsl(240 4.8% 95.9%);
    --border: hsl(240 5.9% 88%);
    --border-hover: hsl(240 5.9% 80%);
    --text: hsl(240 10% 3.9%);
    --text-dim: hsl(240 3.8% 46.1%);
    --text-muted: hsl(240 3.8% 60%);
    --accent: hsl(200 29% 45%);
    --accent-warm: hsl(200 29% 45%);
    --accent-cool: hsl(195 95% 85%);
    --toggle-bg: hsl(240 4.8% 95.9%);
    --toggle-icon: hsl(240 10% 3.9%);
  }}

  [data-theme="dark"] {{
    --bg: hsl(240 20.54% 5.2%);
    --bg-card: hsl(240 10% 3.9%);
    --bg-card-hover: hsl(240 3.7% 15.9%);
    --border: hsl(240 3.7% 15.9%);
    --border-hover: hsl(240 3.7% 25%);
    --text: hsl(0 0% 98%);
    --text-dim: hsl(240 5% 74.9%);
    --text-muted: hsl(240 5% 50%);
    --accent: hsl(195 95% 85%);
    --accent-warm: hsl(195 95% 85%);
    --accent-cool: hsl(195 95% 85%);
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
    transition: background 0.3s ease, color 0.3s ease;
  }}

  .container {{
    max-width: 720px;
    margin: 0 auto;
    padding: 60px 24px;
  }}

  .top-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 48px;
    animation: fadeUp 0.8s ease forwards;
    opacity: 0;
  }}

  .brand {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: var(--text-dim);
    letter-spacing: 3px;
    text-transform: uppercase;
  }}

  .theme-toggle {{
    width: 40px;
    height: 40px;
    border-radius: 10px;
    border: 1px solid var(--border);
    background: var(--toggle-bg);
    color: var(--toggle-icon);
    cursor: pointer;
    display: grid;
    place-items: center;
    transition: all 0.2s ease;
  }}
  .theme-toggle:hover {{
    border-color: var(--border-hover);
    transform: scale(1.05);
  }}
  .theme-toggle svg {{
    width: 18px;
    height: 18px;
    stroke: currentColor;
    stroke-width: 2;
    fill: none;
    stroke-linecap: round;
    stroke-linejoin: round;
  }}

  .site-header {{
    margin-bottom: 48px;
    animation: fadeUp 0.8s ease 0.1s forwards;
    opacity: 0;
  }}
  .site-header h1 {{
    font-size: 42px;
    font-weight: 700;
    letter-spacing: -1px;
    line-height: 1.1;
    margin-bottom: 12px;
  }}
  .site-header h1 span {{
    color: var(--accent);
  }}
  .site-header .subtitle {{
    font-size: 15px;
    color: var(--text-dim);
    max-width: 400px;
  }}

  /* Social / nav links below header */
  .nav-links {{
    display: flex;
    gap: 12px;
    margin-top: 20px;
    animation: fadeUp 0.8s ease 0.15s forwards;
    opacity: 0;
  }}
  .nav-links a {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 14px;
    border-radius: 8px;
    border: 1px solid var(--border);
    background: var(--bg-card);
    color: var(--text-dim);
    text-decoration: none;
    font-size: 12px;
    font-weight: 500;
    transition: all 0.2s ease;
  }}
  .nav-links a:hover {{
    border-color: var(--accent);
    color: var(--accent);
    background: var(--bg-card-hover);
  }}
  .nav-links a svg {{
    width: 14px;
    height: 14px;
    stroke: currentColor;
    stroke-width: 2;
    fill: none;
    stroke-linecap: round;
    stroke-linejoin: round;
  }}

  .featured {{
    margin-bottom: 48px;
    animation: fadeUp 0.8s ease 0.2s forwards;
    opacity: 0;
  }}
  .featured-label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: var(--text-dim);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .featured-label::before {{
    content: '';
    display: inline-block;
    width: 6px;
    height: 6px;
    background: #4ade80;
    border-radius: 50%;
    animation: pulse 2s ease infinite;
  }}
  @keyframes pulse {{
    0%, 100% {{ opacity: 1; box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.4); }}
    50% {{ opacity: 0.7; box-shadow: 0 0 0 6px rgba(74, 222, 128, 0); }}
  }}

  .featured-card {{
    display: block;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 28px;
    text-decoration: none;
    color: inherit;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
  }}
  .featured-card::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
    opacity: 0;
    transition: opacity 0.3s ease;
  }}
  .featured-card:hover {{
    border-color: var(--border-hover);
    background: var(--bg-card-hover);
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.15);
  }}
  .featured-card:hover::before {{
    opacity: 0.6;
  }}
  .featured-card .date {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: var(--accent);
    margin-bottom: 8px;
  }}
  .featured-card .title {{
    font-size: 22px;
    font-weight: 600;
    margin-bottom: 16px;
  }}
  .featured-stats {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
  }}
  .stat {{
    padding: 12px 0;
    border-top: 1px solid var(--border);
  }}
  .stat .num {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 20px;
    font-weight: 700;
    color: var(--text);
  }}
  .stat .lbl {{
    font-size: 11px;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 2px;
  }}

  .archive {{
    animation: fadeUp 0.8s ease 0.3s forwards;
    opacity: 0;
  }}
  .archive-header {{
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    margin-bottom: 16px;
  }}
  .archive-header h2 {{
    font-size: 14px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: var(--text-dim);
  }}
  .archive-count {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: var(--text-muted);
  }}
  .archive-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 12px;
  }}
  .archive-item {{
    display: block;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
    text-decoration: none;
    color: inherit;
    transition: all 0.2s ease;
  }}
  .archive-item:hover {{
    border-color: var(--border-hover);
    background: var(--bg-card-hover);
  }}
  .archive-item .arc-date {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: var(--accent);
    margin-bottom: 6px;
  }}
  .archive-item .arc-title {{
    font-size: 13px;
    font-weight: 500;
    margin-bottom: 8px;
  }}
  .archive-item .arc-meta {{
    font-size: 11px;
    color: var(--text-dim);
    display: flex;
    gap: 12px;
  }}

  .footer {{
    margin-top: 64px;
    padding-top: 24px;
    border-top: 1px solid var(--border);
    text-align: center;
    animation: fadeUp 0.8s ease 0.45s forwards;
    opacity: 0;
  }}
  .footer a {{
    color: var(--text-dim);
    text-decoration: none;
    font-size: 12px;
    transition: color 0.2s;
  }}
  .footer a:hover {{
    color: var(--accent);
  }}

  @keyframes fadeUp {{
    from {{ opacity: 0; transform: translateY(20px); }}
    to {{ opacity: 1; transform: translateY(0); }}
  }}

  @media (max-width: 640px) {{
    .container {{ padding: 32px 16px; }}
    .site-header h1 {{ font-size: 32px; }}
    .featured-stats {{ grid-template-columns: repeat(2, 1fr); gap: 8px; }}
    .stat .num {{ font-size: 16px; }}
    .archive-grid {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>

<div class="container">

  <div class="top-bar">
    <div class="brand">joyehuang.me</div>
    <button class="theme-toggle" id="themeToggle" aria-label="Toggle theme">
      <svg id="moonIcon" viewBox="0 0 24 24"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>
      <svg id="sunIcon" viewBox="0 0 24 24" style="display:none"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>
    </button>
  </div>

  <header class="site-header">
    <h1>AI <span>Usage</span> Report</h1>
    <p class="subtitle">Daily insights from AI-assisted workflows. Hermes Agent sessions + WakaTime coding data.</p>
    <div class="nav-links">
      <a href="https://joyehuang.me" target="_blank">
        <svg viewBox="0 0 24 24"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
        joyehuang.me
      </a>
      <a href="https://github.com/joyehuang" target="_blank">
        <svg viewBox="0 0 24 24"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"/></svg>
        github.com/joyehuang
      </a>
    </div>
  </header>

  <section class="featured">
    <div class="featured-label">Cumulative Overview</div>
{overview_card}
  </section>

  <section class="featured">
    <div class="featured-label">Latest Receipt</div>
{receipt_card}
  </section>

  <section class="featured" style="margin-bottom:32px">
    <div class="featured-label">AI Overview</div>
{dashboard_card}
  </section>

  <section class="archive">
    <div class="archive-header">
      <h2>Daily Receipt Archive</h2>
      <span class="archive-count">{len(archive_items)} reports</span>
    </div>
    <div class="archive-grid">
{archive_grid}    </div>
  </section>

  <section class="archive">
    <div class="archive-header">
      <h2>AI Overview Archive</h2>
      <span class="archive-count">{len(dashboard_archive_items)} weeks</span>
    </div>
    <div class="archive-grid">
{dashboard_archive_grid}    </div>
  </section>

  <footer class="footer">
    <a href="https://joyehuang.me" target="_blank">joyehuang.me</a> ·
    <a href="https://github.com/joyehuang" target="_blank">GitHub</a> ·
    <a href="https://github.com/joyehuang/report" target="_blank">Source</a>
  </footer>

</div>

<script>
(function() {{
  const html = document.documentElement;
  const toggle = document.getElementById('themeToggle');
  const moon = document.getElementById('moonIcon');
  const sun = document.getElementById('sunIcon');

  function setIcon() {{
    const dark = html.getAttribute('data-theme') === 'dark';
    moon.style.display = dark ? 'block' : 'none';
    sun.style.display = dark ? 'none' : 'block';
  }}

  toggle.addEventListener('click', () => {{
    const current = html.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    setIcon();
  }});

  const saved = localStorage.getItem('theme');
  if (saved) {{
    html.setAttribute('data-theme', saved);
  }} else if (window.matchMedia('(prefers-color-scheme: light)').matches) {{
    html.setAttribute('data-theme', 'light');
  }}
  setIcon();
}})();
</script>

</body>
</html>"""

    with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print(f"index.html regenerated with {len(archive_items)} receipts")
    return os.path.join(BASE_DIR, "index.html")


if __name__ == "__main__":
    generate()
