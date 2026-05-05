#!/usr/bin/env python3
"""Generate merged Cache Analysis page (model-level + session-level) at cache.html."""

import os
import sys
import sqlite3
import html as html_lib
from datetime import datetime, timezone, timedelta

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
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


def fetch_data():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Model-level aggregation
    cur.execute("""
        SELECT
            model,
            COUNT(*) as sessions,
            SUM(input_tokens) as input,
            SUM(output_tokens) as output,
            SUM(cache_read_tokens) as cache_read,
            SUM(cache_write_tokens) as cache_write,
            SUM(message_count) as msgs,
            SUM(tool_call_count) as tools
        FROM sessions
        WHERE model IS NOT NULL AND model != ''
        GROUP BY model
        ORDER BY sessions DESC
    """)
    model_rows = cur.fetchall()

    # Overall
    cur.execute("""
        SELECT
            SUM(input_tokens) as input,
            SUM(cache_read_tokens) as cache_read,
            SUM(cache_write_tokens) as cache_write
        FROM sessions
    """)
    overall = cur.fetchone()

    # Session-level data
    cur.execute("""
        SELECT id, model, started_at,
               input_tokens, output_tokens,
               cache_read_tokens, cache_write_tokens,
               message_count, tool_call_count, title
        FROM sessions
        ORDER BY started_at DESC
    """)
    sessions = [dict(r) for r in cur.fetchall()]
    conn.close()

    return model_rows, overall, sessions


def generate():
    model_rows, overall, sessions = fetch_data()

    total_input = overall['input'] or 0
    total_cache_read = overall['cache_read'] or 0
    total_cache_write = overall['cache_write'] or 0
    total_prompt = total_input + total_cache_read
    overall_ratio = (total_cache_read / total_prompt * 100) if total_prompt > 0 else 0

    # Per-session hit ratios
    for s in sessions:
        inp = s["input_tokens"] or 0
        cr = s["cache_read_tokens"] or 0
        denom = inp + cr
        s["hit_ratio"] = (cr / denom * 100) if denom > 0 else 0.0

    total_sessions = len(sessions)
    total_cache_read_s = sum((s["cache_read_tokens"] or 0) for s in sessions)
    total_cache_write_s = sum((s["cache_write_tokens"] or 0) for s in sessions)
    total_input_s = sum((s["input_tokens"] or 0) for s in sessions)
    total_prompt_s = total_input_s + total_cache_read_s
    overall_ratio_s = (total_cache_read_s / total_prompt_s * 100) if total_prompt_s > 0 else 0
    avg_hit_ratio = (
        sum(s["hit_ratio"] for s in sessions) / total_sessions if total_sessions else 0.0
    )

    # --- Model-level sections ---
    # Build ratio bars
    max_ratio = 0
    for row in model_rows:
        inp = row['input'] or 0
        cr = row['cache_read'] or 0
        pt = inp + cr
        r = (cr / pt * 100) if pt > 0 else 0
        if r > max_ratio:
            max_ratio = r

    ratio_bars = ""
    for row in model_rows:
        model = row['model'] or 'unknown'
        inp = row['input'] or 0
        cr = row['cache_read'] or 0
        pt = inp + cr
        ratio = (cr / pt * 100) if pt > 0 else 0
        pct = (ratio / max_ratio * 100) if max_ratio > 0 else 0
        ratio_bars += f"""      <div class="bar-row">
        <span class="bar-label"><code>{html_lib.escape(model)}</code></span>
        <div class="bar-track"><div class="bar-fill" style="width:{pct:.0f}%"></div></div>
        <span class="bar-value">{ratio:.1f}%</span>
      </div>
"""

    # --- Session-level section ---
    models = sorted({(s["model"] or "unknown") for s in sessions})
    filter_buttons = '<button class="filter-btn active" data-model="all">All</button>'
    for m in models:
        filter_buttons += (
            f'<button class="filter-btn" data-model="{html_lib.escape(m)}">'
            f'{html_lib.escape(m)}</button>'
        )

    table_rows = ""
    for s in sessions:
        model = s["model"] or "unknown"
        rc = ratio_class(s["hit_ratio"])
        title = s.get("title") or s["id"]
        title_attr = html_lib.escape(str(title))
        table_rows += f"""      <tr data-model="{html_lib.escape(model)}" title="{title_attr}">
        <td data-label="Started">{fmt_dt(s['started_at'])}</td>
        <td data-label="Model"><code>{html_lib.escape(model)}</code></td>
        <td data-label="Input">{fmt_tokens(s['input_tokens'])}</td>
        <td data-label="Cache Read">{fmt_tokens(s['cache_read_tokens'])}</td>
        <td data-label="Cache Write">{fmt_tokens(s['cache_write_tokens'])}</td>
        <td data-label="Output">{fmt_tokens(s['output_tokens'])}</td>
        <td data-label="Hit Ratio"><span class="ratio {rc}">{s['hit_ratio']:.1f}%</span></td>
        <td data-label="Msgs">{s['message_count'] or 0}</td>
      </tr>
"""

    html = f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Cache Analysis — joyehuang.me</title>
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

  .hero-grid {{
    display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px;
  }}
  .hero {{
    background: var(--card); border: 1px solid var(--border);
    border-radius: 12px; padding: 32px 24px; text-align: center;
  }}
  .hero .big {{
    font-family: 'JetBrains Mono', monospace; font-size: 48px;
    font-weight: 700; color: var(--green);
  }}
  .hero .lbl {{
    font-size: 12px; color: var(--text-dim);
    text-transform: uppercase; letter-spacing: 2px; margin-top: 8px;
  }}
  .hero .sub {{
    font-size: 11px; color: var(--text-muted); margin-top: 6px;
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

  .bar-row {{
    display: flex; align-items: center; gap: 12px;
    padding: 8px 0; font-size: 13px;
  }}
  .bar-label {{
    width: 160px; font-weight: 500; color: var(--text);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }}
  .bar-track {{
    flex: 1; height: 10px; background: var(--border);
    border-radius: 5px; overflow: hidden;
  }}
  .bar-fill {{
    height: 100%; background: var(--green);
    border-radius: 5px; transition: width 0.8s ease;
  }}
  .bar-value {{
    width: 60px; text-align: right;
    font-family: 'JetBrains Mono', monospace; font-size: 12px;
    color: var(--text-dim);
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

  .insight {{
    background: var(--card); border: 1px solid var(--border);
    border-radius: 12px; padding: 20px 24px; margin-bottom: 16px;
    font-size: 13px; color: var(--text-dim); line-height: 1.8;
  }}
  .insight strong {{ color: var(--text); }}

  .footer {{
    margin-top: 40px; padding-top: 20px;
    border-top: 1px solid var(--border); text-align: center;
  }}
  .footer a {{
    color: var(--text-dim); text-decoration: none; font-size: 12px;
    transition: color 0.2s;
  }}
  .footer a:hover {{ color: var(--accent); }}

  /* ─── Mobile Responsive ─── */
  @media (max-width: 768px) {{
    .page {{ padding: 24px 16px; }}
    .header h1 {{ font-size: 28px; }}
    .hero-grid {{ grid-template-columns: 1fr; }}
    .hero .big {{ font-size: 36px; }}
    .grid-3 {{ grid-template-columns: 1fr; }}
    .bar-label {{ width: 100px; }}

    /* Session table → card layout on mobile */
    .data-table#sessionTable thead {{ display: none; }}
    .data-table#sessionTable,
    .data-table#sessionTable tbody,
    .data-table#sessionTable tr,
    .data-table#sessionTable td {{
      display: block;
    }}
    .data-table#sessionTable tr {{
      padding: 12px 8px;
      border-bottom: 1px solid var(--border);
    }}
    .data-table#sessionTable tr:hover td {{ background: transparent; }}
    .data-table#sessionTable td {{
      padding: 4px 0;
      white-space: normal;
      border: none;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .data-table#sessionTable td::before {{
      content: attr(data-label);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: var(--text-dim);
      font-weight: 600;
    }}
    .data-table#sessionTable td[data-label="Started"] {{
      font-weight: 600;
      font-size: 13px;
    }}
  }}

  @media (max-width: 480px) {{
    .page {{ padding: 16px 12px; }}
    .header h1 {{ font-size: 24px; }}
    .hero .big {{ font-size: 30px; }}
    .mini-card .num {{ font-size: 18px; }}
    .filter-btn {{ font-size: 11px; padding: 5px 10px; }}
  }}
</style>
</head>
<body>

<div class="page">
  <div class="top-bar">
    <div class="brand"><a href="index.html" data-i18n="back-home">← AI Usage Report</a></div>
    <div class="top-actions">
      <button class="lang-toggle" id="langToggle" aria-label="Switch language">EN</button>
      <button class="theme-toggle" id="themeToggle" aria-label="Toggle theme">
      <svg class="moon" viewBox="0 0 24 24"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
      <svg class="sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="5"/><path d="M12 1v2"/><path d="M12 21v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M1 12h2"/><path d="M21 12h2"/><path d="m4.93 19.07 1.41-1.41"/><path d="m17.66 6.34 1.41-1.41"/></svg>
    </button>
    </div>
  </div>

  <div class="header">
    <h1 data-i18n="cache-title">Cache <span data-i18n="cache-title-accent">Analysis</span></h1>
    <p class="meta" data-i18n="cache-desc">Hermes Agent prompt caching — model-level overview &amp; per-session breakdown</p>
  </div>

  <div class="hero-grid">
    <div class="hero">
      <div class="big">{overall_ratio:.1f}%</div>
      <div class="lbl" data-i18n="cache-overall-label">Overall Cache Hit Ratio</div>
      <div class="sub">{fmt_tokens(total_cache_read)} cached / {fmt_tokens(total_prompt)} total prompt tokens</div>
    </div>
    <div class="hero">
      <div class="big">{avg_hit_ratio:.1f}%</div>
      <div class="lbl" data-i18n="cache-avg-label">Average Session Hit Ratio</div>
      <div class="sub">{total_sessions} sessions · overall {overall_ratio_s:.1f}%</div>
    </div>
  </div>

  <div class="grid-3">
    <div class="mini-card">
      <div class="num">{fmt_tokens(total_cache_read)}</div>
      <div class="lbl" data-i18n="cache-read">Cache Read</div>
    </div>
    <div class="mini-card">
      <div class="num">{fmt_tokens(total_cache_write)}</div>
      <div class="lbl" data-i18n="cache-write">Cache Write</div>
    </div>
    <div class="mini-card">
      <div class="num">{fmt_tokens(total_input)}</div>
      <div class="lbl" data-i18n="fresh-input">Fresh Input</div>
    </div>
  </div>

  <div class="insight">
    <strong data-i18n="cache-insight-title">About Cache Hit Ratio</strong><br>
    <span>Prompt caching reduces token consumption by reusing previously computed context. A higher <strong>cache_read</strong> means more context reuse, leading to a higher hit ratio and lower costs.</span><br>
    <span>Current data is primarily from the Kimi API, whose OpenAI-compatible interface returns <code>cached_tokens</code> but not <code>cache_write_tokens</code> — hence Cache Write shows as 0. The Anthropic API does report <code>cache_creation_input_tokens</code> separately.</span>
  </div>

  <div class="section">
    <div class="section-title" data-i18n="cache-section-model">Cache Hit Ratio by Model</div>
{ratio_bars}
  </div>

  <div class="section">
    <div class="section-title" data-i18n="cache-section-sessions">All Sessions</div>
    <div class="filter-bar">{filter_buttons}</div>
    <div class="table-wrap">
      <table class="data-table" id="sessionTable">
        <thead>
          <tr>
            <th data-i18n="th-started">Started (Melb)</th>
            <th data-i18n="th-model">Model</th>
            <th data-i18n="th-input">Input</th>
            <th data-i18n="th-cache-read">Cache Read</th>
            <th data-i18n="th-cache-write">Cache Write</th>
            <th data-i18n="th-output">Output</th>
            <th data-i18n="th-hit-ratio">Hit Ratio</th>
            <th data-i18n="th-msgs">Msgs</th>
          </tr>
        </thead>
        <tbody id="sessionsBody">
{table_rows}        </tbody>
      </table>
      <div class="empty" id="emptyMsg" style="display:none"><span data-i18n="cache-filter-empty">No sessions match this filter.</span></div>
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

  // Session filter
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

<script src="assets/i18n.js"></script>
</body>
</html>"""

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, "cache.html")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Cache analysis saved: {filepath}")
    return filepath


if __name__ == "__main__":
    path = generate()
    print(f"OK: {path}")
