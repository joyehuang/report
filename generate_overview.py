#!/usr/bin/env python3
"""Generate simplified cumulative AI Usage Overview page."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.hermes_db import aggregate_all_time
from lib.wakatime_history import get_cumulative
from lib.cost_tracker import get_summary

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


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


def generate():
    # Hermes Agent all-time stats (Dashboard 口径: input + output only)
    hermes = aggregate_all_time()
    hermes_tokens = hermes.get("total_input", 0) + hermes.get("total_output", 0)
    hermes_cache_read = hermes.get("total_cache_read", 0)
    hermes_cache_write = hermes.get("total_cache_write", 0)
    total_prompt = hermes.get("total_input", 0) + hermes_cache_read
    cache_hit_ratio = (hermes_cache_read / total_prompt * 100) if total_prompt > 0 else 0

    # WakaTime cumulative stats
    waka = get_cumulative()
    waka_tokens = waka.get("total_ai_in", 0) + waka.get("total_ai_out", 0)

    # Grand total (Hermes input+output + WakaTime, cache excluded)
    grand_tokens = hermes_tokens + waka_tokens
    grand_cost = get_summary()
    ai_cost = grand_cost["ai"]
    svc_cost = grand_cost["services"]
    combined_total = grand_cost["combined_total"]

    # Combined cost subtitle (e.g. "Token Cost $280 + Service Cost $143")
    combined_sub_args = [f"{ai_cost['total_usd']:.0f}", f"{svc_cost['total_usd']:.0f}"]
    combined_sub_text = f"Token Cost ${combined_sub_args[0]} + Service Cost ${combined_sub_args[1]}"

    # Build stat cards (only 3 as requested) — tuple: (label, value, sub, label_i18n_key, sub_i18n_key, sub_args)
    stat_cards = [
        ("Total Tokens", fmt_tokens(grand_tokens), f"Hermes {fmt_tokens(hermes_tokens)} + WakaTime {fmt_tokens(waka_tokens)}", "overview-total-tokens", None, None),
        ("Total Cost", f"${combined_total:.2f}", combined_sub_text, "overview-total-cost", "overview-cost-combined", combined_sub_args),
        ("Coding Time", fmt_duration(waka.get("total_seconds", 0)), "Total coding hours", "overview-coding-time", "overview-coding-sub", None),
    ]

    # Provider cost bars (AI only)
    provider_bars = ""
    if ai_cost.get("by_provider"):
        max_cost = max(v["cost_usd"] for v in ai_cost["by_provider"].values())
        for provider, data in sorted(ai_cost["by_provider"].items(), key=lambda x: -x[1]["cost_usd"]):
            pct = (data["cost_usd"] / max_cost) * 100
            provider_bars += f"""      <div class="bar-row">
        <span class="bar-label">{provider.title()}</span>
        <div class="bar-track"><div class="bar-fill" style="width:{pct:.0f}%"></div></div>
        <span class="bar-value">${data['cost_usd']:.2f}</span>
      </div>
"""

    # Monthly cost table (AI only)
    month_rows = ""
    if ai_cost.get("by_month"):
        for month, data in sorted(ai_cost["by_month"].items(), reverse=True):
            month_rows += f"""      <tr>
        <td>{month}</td>
        <td>${data['cost_usd']:.2f}</td>
      </tr>
"""

    # Service costs table — Service | Monthly Cost (latest month) | Total
    service_rows = ""
    svc_months_sorted = sorted(svc_cost.get("by_month", {}).keys(), reverse=True)
    latest_svc_month = svc_months_sorted[0] if svc_months_sorted else None
    if svc_cost.get("by_service"):
        for service, sdata in sorted(svc_cost["by_service"].items(), key=lambda x: -x[1]["cost_usd"]):
            latest_month_cost = 0.0
            if latest_svc_month:
                for entry in sdata["entries"]:
                    if entry["month"] == latest_svc_month:
                        latest_month_cost += entry["cost_usd"]
            service_rows += f"""      <tr>
        <td>{service.title()}</td>
        <td>${latest_month_cost:.2f}</td>
        <td>${sdata['cost_usd']:.2f}</td>
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
  .page {{ max-width: 720px; margin: 0 auto; padding: 40px 24px; }}

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

  .top-actions {{ display: flex; gap: 8px; align-items: center; }}
  .lang-toggle {{
    width: 44px; height: 40px; border-radius: 10px;
    border: 1px solid var(--border); background: var(--toggle-bg);
    color: var(--toggle-icon); cursor: pointer;
    font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 600;
    letter-spacing: 1px; transition: all 0.2s ease;
  }}
  .lang-toggle:hover {{ transform: scale(1.05); border-color: var(--accent); }}

  .header {{ margin-bottom: 32px; }}
  .header h1 {{ font-size: 36px; font-weight: 700; letter-spacing: -1px; }}
  .header h1 span {{ color: var(--accent); }}
  .header .meta {{
    font-size: 13px; color: var(--text-dim); margin-top: 8px;
  }}

  .stats-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px; margin-bottom: 24px;
  }}
  .stat-card {{
    background: var(--card); border: 1px solid var(--border);
    border-radius: 10px; padding: 24px 16px; text-align: center;
    transition: all 0.2s ease;
  }}
  .stat-card:hover {{
    border-color: var(--accent); transform: translateY(-2px);
  }}
  .stat-card .num {{
    font-family: 'JetBrains Mono', monospace; font-size: 28px;
    font-weight: 700; color: var(--text);
  }}
  .stat-card .lbl {{
    font-size: 11px; color: var(--text-dim);
    text-transform: uppercase; letter-spacing: 1px; margin-top: 6px;
  }}
  .stat-card .sub {{
    font-size: 10px; color: var(--text-muted); margin-top: 4px;
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
    .stats-grid {{ grid-template-columns: 1fr; }}
    .bar-label {{ width: 80px; }}
  }}
</style>
</head>
<body>

<div class="page">
  <div class="top-bar">
    <div class="brand"><a href="./index.html" data-i18n="back-home">← AI Usage Report</a></div>
    <div class="top-actions">
      <button class="lang-toggle" id="langToggle" aria-label="Switch language">EN</button>
      <button class="theme-toggle" id="themeToggle" aria-label="Toggle theme">
      <svg class="moon" viewBox="0 0 24 24"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
      <svg class="sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="5"/><path d="M12 1v2"/><path d="M12 21v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M1 12h2"/><path d="M21 12h2"/><path d="m4.93 19.07 1.41-1.41"/><path d="m17.66 6.34 1.41-1.41"/></svg>
    </button>
    </div>
  </div>

  <div class="header">
    <h1><span data-i18n="overview-title">Cumulative</span> <span data-i18n="overview-title-accent">Overview</span></h1>
    <p class="meta"><span data-i18n="overview-meta-stats">Cumulative stats</span> · {days_recorded} <span data-i18n="overview-meta-days">days recorded</span> · {date_range}</p>
  </div>

  <div class="stats-grid">
"""

    for label, value, sub, label_key, sub_key, sub_args in stat_cards:
        sub_attr = f' data-i18n="{sub_key}"' if sub_key else ''
        if sub_args is not None:
            import json as _json
            sub_attr += f' data-i18n-args=\'{_json.dumps(sub_args)}\''
        html += f"""    <div class="stat-card">
      <div class="num">{value}</div>
      <div class="lbl" data-i18n="{label_key}">{label}</div>
      <div class="sub"{sub_attr}>{sub}</div>
    </div>
"""

    no_cost_msg = '    <p style="color:var(--text-muted);font-size:13px;" data-i18n="overview-no-cost-data">No cost data yet.</p>'
    html += f"""  </div>

  <div class="section">
    <div class="section-title" data-i18n="overview-cost-provider">Cost by Provider</div>
{provider_bars or no_cost_msg}
  </div>

"""

    # Service Costs section (moved above Monthly Cost)
    if service_rows:
        svc_total_text = f"${svc_cost['total_usd']:.2f}"
        html += f"""  <div class="section">
    <div class="section-title" data-i18n="overview-service-costs">Service Costs</div>
    <p style="font-size:12px;color:var(--text-muted);margin-bottom:4px;" data-i18n="overview-service-costs-desc">Infrastructure &amp; hosting services</p>
    <p style="font-size:12px;color:var(--text-dim);margin-bottom:12px;font-family:'JetBrains Mono',monospace;"><span data-i18n="overview-total-label">Total</span>: {svc_total_text}</p>
    <table class="cost-table">
      <thead>
        <tr><th data-i18n="stat-service">Service</th><th data-i18n="stat-monthly-cost">Monthly Cost</th><th data-i18n="stat-total">Total</th></tr>
      </thead>
      <tbody>
{service_rows}      </tbody>
    </table>
  </div>
"""

    if month_rows:
        html += f"""  <div class="section">
    <div class="section-title" data-i18n="overview-monthly-cost">Monthly Cost</div>
    <table class="cost-table">
      <thead>
        <tr><th data-i18n="overview-month">Month</th><th data-i18n="overview-cost">Cost</th></tr>
      </thead>
      <tbody>
{month_rows}      </tbody>
    </table>
  </div>
"""

    # Cache stats section
    html += f"""  <div class="section">
    <div class="section-title" data-i18n="overview-cache-section-title">Hermes Agent Cache</div>
    <div class="stats-grid" style="grid-template-columns: repeat(3, 1fr); margin-bottom: 0;">
      <div class="stat-card" style="border: none; padding: 16px;">
        <div class="num">{fmt_tokens(hermes_cache_read)}</div>
        <div class="lbl" data-i18n="stat-cache-read">Cache Read</div>
      </div>
      <div class="stat-card" style="border: none; padding: 16px;">
        <div class="num">{fmt_tokens(hermes_cache_write)}</div>
        <div class="lbl" data-i18n="stat-cache-write">Cache Write</div>
      </div>
      <div class="stat-card" style="border: none; padding: 16px;">
        <div class="num">{cache_hit_ratio:.1f}%</div>
        <div class="lbl" data-i18n="stat-hit-ratio">Hit Ratio</div>
      </div>
    </div>
    <p style="margin-top: 12px; font-size: 12px; color: var(--text-muted);">
      <a href="cache.html" style="color: var(--accent); text-decoration: none;"><span data-i18n="overview-cache-link">→ View cache analysis</span></a>
    </p>
  </div>
"""

    html += f"""
  <div class="footer">
    <a href="https://joyehuang.me" target="_blank" data-i18n="footer-joye">joyehuang.me</a> ·
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

<script src="assets/i18n.js"></script>
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
