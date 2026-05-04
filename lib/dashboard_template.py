"""HTML template renderer for the AI Overview dashboard."""


def render_dashboard(**data):
    date_range = data["date_range"]
    total_time = data["total_time"]
    categories = data["categories"]
    editors = data["editors"]
    ai_input = data.get("ai_input", 0)
    ai_output = data.get("ai_output", 0)
    ai_prompts = data.get("ai_prompts", 0)
    hermes_input = data["hermes_input"]
    hermes_output = data["hermes_output"]
    hermes_cache = data["hermes_cache"]
    session_count = data["session_count"]
    total_tokens = hermes_input + hermes_output + hermes_cache

    def fmt_tok(n):
        if n >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        elif n >= 1_000:
            return f"{n/1_000:.1f}K"
        return str(n)

    # Category bars
    max_cat = max(c["total_seconds"] for c in categories) if categories else 1
    cat_bars = ""
    for cat in categories:
        pct = (cat["total_seconds"] / max_cat) * 100
        cat_bars += f"""      <div class="bar-item">
        <div class="bar-head">
          <span>{cat['name']}</span>
          <span class="bar-value">{cat['text']}</span>
        </div>
        <div class="track"><div class="fill" style="width:{pct:.0f}%"></div></div>
      </div>
"""

    # Editor pills
    editor_pills = ""
    for ed in editors[:4]:
        editor_pills += f"""        <span class="pill">{ed['name']} {ed['text']}</span>
"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Overview — {date_range}</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: hsl(240 20.54% 5.2%);
    --bg-card: hsl(240 10% 3.9%);
    --bg-card-hover: hsl(240 3.7% 15.9%);
    --border: hsl(240 3.7% 15.9%);
    --border-hover: hsl(240 3.7% 25%);
    --text: hsl(0 0% 98%);
    --text-dim: hsl(240 5% 74.9%);
    --text-muted: hsl(240 5% 50%);
    --accent: hsl(195 95% 85%);
    --accent-soft: hsl(195 70% 20%);
    --green: hsl(142 60% 65%);
  }}

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    font-family: 'Inter', system-ui, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.5;
    min-height: 100vh;
    -webkit-font-smoothing: antialiased;
  }}

  .page {{
    max-width: 900px;
    margin: 0 auto;
    padding: 40px 24px;
  }}

  .header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 24px;
    margin-bottom: 32px;
    flex-wrap: wrap;
  }}

  .eyebrow {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: var(--text-muted);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 8px;
  }}

  h1 {{
    font-size: 36px;
    font-weight: 700;
    letter-spacing: -0.5px;
  }}

  .subtitle {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    margin-top: 8px;
    color: var(--text-dim);
    font-size: 14px;
  }}
  .dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--accent);
  }}

  .date-pill {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 8px 16px;
    font-size: 13px;
    color: var(--text-dim);
    background: var(--bg-card);
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
  }}

  .card {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 16px;
  }}

  .card-title {{
    font-size: 13px;
    font-weight: 600;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 16px;
  }}

  .main-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }}

  .donut-wrap {{
    position: relative;
    width: 180px;
    aspect-ratio: 1;
    display: grid;
    place-items: center;
    margin: 0 auto;
  }}
  .donut-svg {{
    width: 100%;
    height: 100%;
    transform: rotate(-90deg);
  }}
  .donut-bg, .donut-ring {{
    fill: none;
    stroke-width: 18;
  }}
  .donut-bg {{ stroke: var(--border); }}
  .donut-ring {{
    stroke: var(--accent);
    stroke-linecap: round;
    stroke-dasharray: 471;
    stroke-dashoffset: 0;
  }}
  .donut-center {{
    position: absolute;
    text-align: center;
  }}
  .donut-center strong {{
    display: block;
    font-size: 36px;
    font-weight: 700;
    color: var(--text);
  }}
  .donut-center span {{
    display: block;
    font-size: 12px;
    color: var(--text-muted);
    margin-top: 4px;
  }}

  .big-stat {{
    text-align: center;
    padding: 20px 0;
  }}
  .big-stat .num {{
    font-size: 42px;
    font-weight: 700;
    color: var(--accent);
    font-family: 'JetBrains Mono', monospace;
  }}
  .big-stat .lbl {{
    font-size: 11px;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 4px;
  }}

  .bar-item {{
    margin: 12px 0;
  }}
  .bar-head {{
    display: flex;
    justify-content: space-between;
    font-size: 13px;
    margin-bottom: 6px;
  }}
  .bar-value {{
    font-weight: 600;
    color: var(--text);
  }}
  .track {{
    height: 10px;
    background: var(--border);
    border-radius: 999px;
    overflow: hidden;
  }}
  .fill {{
    height: 100%;
    background: var(--accent);
    border-radius: 999px;
    transition: width 1s ease;
  }}

  .metric-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
  }}
  .metric-card {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
  }}
  .metric-icon {{
    width: 32px;
    height: 32px;
    border-radius: 8px;
    background: var(--accent-soft);
    color: var(--accent);
    display: grid;
    place-items: center;
    margin-bottom: 12px;
    font-size: 14px;
  }}
  .metric-label {{
    font-size: 11px;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1px;
  }}
  .metric-value {{
    font-size: 28px;
    font-weight: 700;
    margin-top: 4px;
    color: var(--text);
  }}
  .metric-sub {{
    font-size: 12px;
    color: var(--text-dim);
    margin-top: 4px;
  }}

  .pill {{
    display: inline-block;
    padding: 4px 10px;
    border-radius: 999px;
    background: var(--bg-card-hover);
    border: 1px solid var(--border);
    font-size: 11px;
    color: var(--text-dim);
    margin: 2px;
  }}

  .footer {{
    text-align: center;
    margin-top: 32px;
    padding-top: 16px;
    border-top: 1px solid var(--border);
    font-size: 11px;
    color: var(--text-muted);
  }}
  .footer a {{ color: var(--text-dim); text-decoration: none; }}
  .footer a:hover {{ color: var(--accent); }}

  @media (max-width: 720px) {{
    .main-grid {{ grid-template-columns: 1fr; }}
    .metric-grid {{ grid-template-columns: 1fr; }}
    h1 {{ font-size: 28px; }}
  }}
</style>
</head>
<body>

<div class="page">

  <div class="header">
    <div>
      <div class="eyebrow">Intelligence Dashboard</div>
      <h1>AI Overview</h1>
      <div class="subtitle"><span class="dot"></span>Personal activity</div>
    </div>
    <div class="date-pill">{date_range}</div>
  </div>

  <div class="main-grid">
    <div class="card">
      <div class="card-title">Coding Time</div>
      <div class="big-stat">
        <div class="num">{total_time}</div>
        <div class="lbl">Total Time</div>
      </div>
      {cat_bars}
    </div>

    <div class="card">
      <div class="card-title">Editors</div>
      <div style="margin-top:8px">
        {editor_pills}
      </div>
      <div class="card-title" style="margin-top:24px">AI Prompts (WakaTime)</div>
      <div class="big-stat" style="padding:12px 0">
        <div class="num">{ai_prompts}</div>
        <div class="lbl">Prompt Events</div>
      </div>
    </div>
  </div>

  <div class="metric-grid">
    <div class="metric-card">
      <div class="metric-icon">💵</div>
      <div class="metric-label">Hermes Input</div>
      <div class="metric-value">{fmt_tok(hermes_input)}</div>
      <div class="metric-sub">AI tokens sent</div>
    </div>
    <div class="metric-card">
      <div class="metric-icon">⚙️</div>
      <div class="metric-label">Hermes Output</div>
      <div class="metric-value">{fmt_tok(hermes_output)}</div>
      <div class="metric-sub">AI tokens received</div>
    </div>
    <div class="metric-card">
      <div class="metric-icon">✏️</div>
      <div class="metric-label">Cache Read</div>
      <div class="metric-value">{fmt_tok(hermes_cache)}</div>
      <div class="metric-sub">KV cache hits</div>
    </div>
  </div>

  <div class="footer">
    <div>Generated by Hermes Agent · {date_range}</div>
    <div><a href="https://report.joyehuang.me">report.joyehuang.me</a> · <a href="https://github.com/joyehuang/report">GitHub</a></div>
  </div>

</div>

</body>
</html>"""
