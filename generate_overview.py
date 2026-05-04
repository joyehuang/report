#!/usr/bin/env python3
"""Generate cumulative AI Usage Overview page."""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.hermes_db import aggregate_all_time
from lib.wakatime_history import get_cumulative
from lib.cost_tracker import get_summary

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "archive")


def fmt_tokens(n):
    if n >= 1_000_000_000:
        return f"{n/1_000_000_000:.2f}B"
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def fmt_duration(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    return f"{h}h {m:02d}m"


def fmt_number(n):
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def generate():
    # Hermes Agent all-time stats
    hermes = aggregate_all_time()
    total_tokens = (hermes.get("total_input", 0) + hermes.get("total_output", 0) +
                    hermes.get("total_cache_read", 0) + hermes.get("total_cache_write", 0) +
                    hermes.get("total_reasoning", 0))

    # WakaTime cumulative stats
    waka = get_cumulative()

    # Cost stats
    cost_data = get_summary()

    # Build stat cards
    stat_cards = [
        ("Cost", f"${cost_data['total_usd']:.2f}", "USD spent on AI"),
        ("Coding Time", fmt_duration(waka.get("total_seconds", 0)), "Total coding hours"),
        ("Tokens", fmt_tokens(total_tokens), "Hermes Agent tokens"),
        ("Prompts", fmt_number(waka.get("total_prompts", 0)), "AI prompts sent"),
        ("Messages", fmt_number(hermes.get("total_msgs", 0)), "Hermes Agent messages"),
        ("Tool Calls", fmt_number(hermes.get("total_tools", 0)), "Hermes Agent tools"),
        ("Sessions", fmt_number(hermes.get("session_count", 0)), "Hermes Agent sessions"),
    ]

    # Provider cost bars
    provider_bars = ""
    if cost_data.get("by_provider"):
        max_cost = max(v["cost_usd"] for v in cost_data["by_provider"].values())
        for provider, data in sorted(cost_data["by_provider"].items(), key=lambda x: -x[1]["cost_usd"]):
            pct = (data["cost_usd"] / max_cost) * 100
            provider_bars += f"""      <div class="bar-row">
        <span class="bar-label">{provider.title()}</span>
        <div class="bar-track"><div class="bar-fill" style="width:{pct:.0f}%"></div></div>
        <span class="bar-value">${data['cost_usd']:.2f}</span>
      </div>
"""

    # Model distribution
    model_bars = ""
    if hermes.get("models"):
        max_model = max(hermes["models"].values())
        for model, count in hermes["models"].most_common(8):
            pct = (count / max_model) * 100
            model_bars += f"""      <div class="bar-row">
        <span class="bar-label">{model}</span>
        <div class="bar-track"><div class="bar-fill" style="width:{pct:.0f}%"></div></div>
        <span class="bar-value">{count}</span>
      </div>
"""

    # Platform distribution
    platform_bars = ""
    if hermes.get("sources"):
        max_src = max(hermes["sources"].values())
        for src, count in hermes["sources"].most_common():
            pct = (count / max_src) * 100
            platform_bars += f"""      <div class="bar-row">
        <span class="bar-label">{src.upper()}</span>
        <div class="bar-track"><div class="bar-fill" style="width:{pct:.0f}%"></div></div>
        <span class="bar-value">{count}</span>
      </div>
"""

    # Monthly cost table
    month_rows = ""
    if cost_data.get("by_month"):
        for month, data in sorted(cost_data["by_month"].items(), reverse=True):
            month_rows += f"""      <tr>
        <td>{month}</td>
        <td>${data['cost_usd']:.2f}</td>
        <td>{', '.join(set(data['entries'][0]['provider'] for e in data['entries']))}</td>
      </tr>
"""

    date_range = waka.get("date_range", "")
    days_recorded = waka.get("days_recorded", 0)

    html = f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Usage Overview — joyehuang.me</title>
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
  .page {{ max-width: 900px; margin: 0 auto; padding: 40px 24px; }}

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

  .stats-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 12px; margin-bottom: 32px;
  }}
  .stat-card {{
    background: var(--card); border: 1px solid var(--border);
    border-radius: 10px; padding: 20px 16px; text-align: center;
    transition: all 0.2s ease;
  }}
  .stat-card:hover {{
    border-color: var(--accent); transform: translateY(-2px);
  }}
  .stat-card .num {{
    font-family: 'JetBrains Mono', monospace; font-size: 24px;
    font-weight: 700; color: var(--text);
  }}
  .stat-card .lbl {{
    font-size: 11px; color: var(--text-dim);
    text-transform: uppercase; letter-spacing: 1px; margin-top: 4px;
  }}
  .stat-card .sub {{
    font-size: 11px; color: var(--text-muted); margin-top: 2px;
  }}

  .section {{
    background: var(--card); border: 1px solid var(--border);
    border-radius: 12px; padding: 24px; margin-bottom: 16px;
  }}
  .section-title {{
    font-size: 14px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 2px; color: var(--text-dim); margin-bottom: 16px;
  }}

  .bar-row {{
    display: flex; align-items: center; gap: 12px;
    padding: 8px 0; font-size: 13px;
  }}
  .bar-label {{
    width: 120px; font-weight: 500; color: var(--text);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }}
  .bar-track {{
    flex: 1; height: 10px; background: var(--border);
    border-radius: 5px; overflow: hidden;
  }}
  .bar-fill {{
    height: 100%; background: var(--accent);
    border-radius: 5px; transition: width 0.8s ease;
  }}
  .bar-value {{
    width: 70px; text-align: right;
    font-family: 'JetBrains Mono', monospace; font-size: 12px;
    color: var(--text-dim);
  }}

  .cost-table {{
    width: 100%; border-collapse: collapse; font-size: 13px;
  }}
  .cost-table th, .cost-table td {{
    text-align: left; padding: 10px 12px;
    border-bottom: 1px solid var(--border);
  }}
  .cost-table th {{
    font-size: 11px; text-transform: uppercase; letter-spacing: 1px;
    color: var(--text-dim); font-weight: 600;
  }}
  .cost-table td {{ color: var(--text); }}
  .cost-table tr:hover td {{ background: var(--accent-soft); }}

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
    .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
    .bar-label {{ width: 80px; }}
  }}
</style>
</head>
<body>

<div class="page">
  <div class="top-bar">
    <div class="brand"><a href="./index.html">← AI Usage Report</a></div>
    <button class="theme-toggle" id="themeToggle" aria-label="Toggle theme">
      <svg class="moon" viewBox="0 0 24 24"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
      <svg class="sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="5"/><path d="M12 1v2"/><path d="M12 21v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M1 12h2"/><path d="M21 12h2"/><path d="m4.93 19.07 1.41-1.41"/><path d="m17.66 6.34 1.41-1.41"/></svg>
    </button>
  </div>

  <div class="header">
    <h1>AI <span>Overview</span></h1>
    <p class="meta">Cumulative stats · {days_recorded} days recorded · {date_range}</p>
  </div>

  <div class="stats-grid">
"""

    for label, value, sub in stat_cards:
        html += f"""    <div class="stat-card">
      <div class="num">{value}</div>
      <div class="lbl">{label}</div>
      <div class="sub">{sub}</div>
    </div>
"""

    html += f"""  </div>

  <div class="section">
    <div class="section-title">Cost by Provider</div>
{provider_bars or '    <p style="color:var(--text-muted);font-size:13px;">No cost data yet.</p>'}
  </div>

  <div class="section">
    <div class="section-title">Model Distribution</div>
{model_bars or '    <p style="color:var(--text-muted);font-size:13px;">No model data.</p>'}
  </div>

  <div class="section">
    <div class="section-title">Platform Distribution</div>
{platform_bars or '    <p style="color:var(--text-muted);font-size:13px;">No platform data.</p>'}
  </div>

"""

    if month_rows:
        html += f"""  <div class="section">
    <div class="section-title">Monthly Cost</div>
    <table class="cost-table">
      <thead>
        <tr><th>Month</th><th>Cost</th><th>Providers</th></tr>
      </thead>
      <tbody>
{month_rows}      </tbody>
    </table>
  </div>
"""

    html += f"""
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
}})();
</script>

</body>
</html>"""

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, "overview.html")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Overview saved: {filepath}")
    return filepath


if __name__ == "__main__":
    path = generate()
    print(f"OK: {path}")
