#!/usr/bin/env python3
"""Generate Hermes Agent Cache Analysis page (model-level comparison)."""

import os
import sys
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "archive")
DB_PATH = os.path.expanduser("~/.hermes/state.db")


def fmt_tokens(n):
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def get_model_cache_stats():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
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
    rows = cur.fetchall()

    # Overall
    cur.execute("""
        SELECT 
            SUM(input_tokens) as input,
            SUM(cache_read_tokens) as cache_read,
            SUM(cache_write_tokens) as cache_write
        FROM sessions
    """)
    overall = cur.fetchone()
    conn.close()
    return rows, overall


def generate():
    rows, overall = get_model_cache_stats()

    total_input = overall['input'] or 0
    total_cache_read = overall['cache_read'] or 0
    total_cache_write = overall['cache_write'] or 0
    total_prompt = total_input + total_cache_read
    overall_ratio = (total_cache_read / total_prompt * 100) if total_prompt > 0 else 0

    # Build model rows
    model_rows = ""
    for row in rows:
        model = row['model'] or 'unknown'
        input_t = row['input'] or 0
        cache_r = row['cache_read'] or 0
        cache_w = row['cache_write'] or 0
        output_t = row['output'] or 0
        prompt_total = input_t + cache_r
        ratio = (cache_r / prompt_total * 100) if prompt_total > 0 else 0
        model_rows += f"""      <tr>
        <td><code>{model}</code></td>
        <td>{row['sessions']}</td>
        <td>{fmt_tokens(input_t)}</td>
        <td>{fmt_tokens(cache_r)}</td>
        <td>{fmt_tokens(cache_w)}</td>
        <td>{fmt_tokens(output_t)}</td>
        <td><span class="ratio">{ratio:.1f}%</span></td>
      </tr>
"""

    # Build ratio bars
    ratio_bars = ""
    max_ratio = 0
    for row in rows:
        input_t = row['input'] or 0
        cache_r = row['cache_read'] or 0
        prompt_total = input_t + cache_r
        ratio = (cache_r / prompt_total * 100) if prompt_total > 0 else 0
        if ratio > max_ratio:
            max_ratio = ratio

    for row in rows:
        model = row['model'] or 'unknown'
        input_t = row['input'] or 0
        cache_r = row['cache_read'] or 0
        prompt_total = input_t + cache_r
        ratio = (cache_r / prompt_total * 100) if prompt_total > 0 else 0
        pct = (ratio / max_ratio * 100) if max_ratio > 0 else 0
        ratio_bars += f"""      <div class="bar-row">
        <span class="bar-label"><code>{model}</code></span>
        <div class="bar-track"><div class="bar-fill" style="width:{pct:.0f}%"></div></div>
        <span class="bar-value">{ratio:.1f}%</span>
      </div>
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
    --green: hsl(142 60% 45%);
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

  .data-table {{
    width: 100%; border-collapse: collapse; font-size: 13px;
  }}
  .data-table th, .data-table td {{
    text-align: left; padding: 10px 12px;
    border-bottom: 1px solid var(--border);
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
    color: var(--green);
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

  @media (max-width: 640px) {{
    .page {{ padding: 24px 16px; }}
    .header h1 {{ font-size: 28px; }}
    .hero .big {{ font-size: 40px; }}
    .grid-3 {{ grid-template-columns: 1fr; }}
    .bar-label {{ width: 100px; }}
    .data-table {{ font-size: 11px; }}
    .data-table th, .data-table td {{ padding: 8px 6px; }}
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
    <h1>Cache <span>Analysis</span></h1>
    <p class="meta">Hermes Agent prompt caching stats by model</p>
  </div>

  <div class="hero">
    <div class="big">{overall_ratio:.1f}%</div>
    <div class="lbl">Overall Cache Hit Ratio</div>
    <div class="sub">{fmt_tokens(total_cache_read)} cached / {fmt_tokens(total_prompt)} total prompt tokens</div>
  </div>

  <div class="grid-3">
    <div class="mini-card">
      <div class="num">{fmt_tokens(total_cache_read)}</div>
      <div class="lbl">Cache Read</div>
    </div>
    <div class="mini-card">
      <div class="num">{fmt_tokens(total_cache_write)}</div>
      <div class="lbl">Cache Write</div>
    </div>
    <div class="mini-card">
      <div class="num">{fmt_tokens(total_input)}</div>
      <div class="lbl">Fresh Input</div>
    </div>
  </div>

  <div class="insight">
    <strong>关于 Cache Hit Ratio</strong><br>
    Prompt caching 是通过重用之前的 prompt 上下文来减少 token 消耗。当 <strong>cache_read</strong> 越高，说明越多的上下文被重用，hit ratio 越高，成本越低。<br>
    Anthropic Claude 和 Kimi 都支持 prompt caching，但各模型的缓存策略和命中率可能不同。
  </div>

  <div class="section">
    <div class="section-title">Cache Hit Ratio by Model</div>
{ratio_bars}
  </div>

  <div class="section">
    <div class="section-title">Model Breakdown</div>
    <table class="data-table">
      <thead>
        <tr>
          <th>Model</th>
          <th>Sessions</th>
          <th>Input</th>
          <th>Cache Read</th>
          <th>Cache Write</th>
          <th>Output</th>
          <th>Hit Ratio</th>
        </tr>
      </thead>
      <tbody>
{model_rows}
      </tbody>
    </table>
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
}})();
</script>

</body>
</html>"""

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, "cache-analysis.html")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Cache analysis saved: {filepath}")
    return filepath


if __name__ == "__main__":
    path = generate()
    print(f"OK: {path}")
