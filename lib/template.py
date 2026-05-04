"""HTML template renderer for the daily receipt."""


def render_receipt(**data):
    date_str = data["date_str"]
    display_date = data["display_date"]
    session_count = data["session_count"]
    total_tools = data["total_tools"]
    total_msgs = data["total_msgs"]
    fmt = data["format_tokens"]
    fdur = data["format_duration"]

    total_fmt = fmt(data["total_tokens"])
    input_fmt = fmt(data["total_input"])
    output_fmt = fmt(data["total_output"])
    cache_r_fmt = fmt(data["total_cache_read"])
    cache_w_fmt = fmt(data["total_cache_write"])
    reason_fmt = fmt(data["total_reasoning"])

    # Models
    max_model = max(data["models"].values()) if data["models"] else 1
    model_rows = ""
    for model, count in data["models"].most_common():
        pct = (count / max_model) * 100
        model_rows += f"""      <div class="model-bar">
        <span class="model-name">{model}</span>
        <div class="model-bar-fill"><div class="model-bar-inner" style="width:{pct:.0f}%"></div></div>
        <span class="model-count">{count}</span>
      </div>
"""

    # Platforms
    platform_rows = ""
    for src, count in data["sources"].most_common():
        msgs_for_src = sum(
            s["message_count"] or 0 for s in data["sessions"] if s["source"] == src
        )
        platform_rows += f"""      <div class="row">
        <span class="label">{src.upper()}</span>
        <span class="value">{count} sessions / {msgs_for_src} msgs</span>
      </div>
"""

    # Sessions
    session_rows = ""
    for s in data["sessions"]:
        dur = fdur((s["ended_at"] or s["started_at"]) - s["started_at"])
        title = (s["title"] or "Untitled")[:35]
        session_rows += f"""      <div class="session-item">
        <div class="session-main">
          <span class="session-time">{dur}</span>
          <span class="session-source">{s['source']}</span>
        </div>
        <div class="session-title">{title}</div>
      </div>
"""

    # Top tools
    tool_rows = ""
    for i, (tool, count) in enumerate(data["top_tools"], 1):
        tool_rows += f"""      <div class="row">
        <span class="tool-name">#{i} {tool}</span>
        <span class="tool-count">{count} calls</span>
      </div>
"""

    # WakaTime
    waka_section = ""
    waka = data.get("waka")
    if waka:
        coding_time = waka["total_text"]
        cat_rows = ""
        for cat in waka["categories"]:
            cat_rows += f"""        <div class="waka-cat">
          <span class="waka-dot"></span>
          <span class="waka-name">{cat['name']}</span>
          <span class="waka-val">{cat['text']}</span>
        </div>
"""
        waka_section = f"""    <div class="section">
      <div class="section-title">\u25a0 Coding Activity</div>
      <div class="waka-main">
        <div class="waka-big">{coding_time}</div>
        <div class="waka-sublabel">Total Time</div>
      </div>
      <div class="waka-cats">
{cat_rows}      </div>
    </div>
"""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Joye's Daily Receipt \u2014 {date_str}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg-body: hsl(240 20.54% 5.2%);
    --bg-receipt: hsl(240 10% 3.9%);
    --text-primary: hsl(0 0% 98%);
    --text-secondary: hsl(240 5% 74.9%);
    --text-muted: hsl(240 5% 50%);
    --accent: hsl(195 95% 85%);
    --accent-cool: hsl(195 95% 85%);
    --border: hsl(240 3.7% 15.9%);
    --border-dashed: hsl(240 3.7% 15.9%);
    --card-bg: hsl(240 3.7% 15.9%);
    --bar-bg: hsl(240 3.7% 15.9%);
    --bar-fill: hsl(195 95% 85%);
    --printer-led: hsl(142 60% 65%);
  }}

  @media (prefers-color-scheme: light) {{
    :root {{
      --bg-body: hsl(210 33% 99%);
      --bg-receipt: hsl(0 0% 100%);
      --text-primary: hsl(240 10% 3.9%);
      --text-secondary: hsl(240 3.8% 46.1%);
      --text-muted: hsl(240 3.8% 46.1%);
      --accent: hsl(200 29% 45%);
      --accent-cool: hsl(200 29% 45%);
      --border: hsl(240 5.9% 88%);
      --border-dashed: hsl(240 5.9% 88%);
      --card-bg: hsl(240 4.8% 95.9%);
      --bar-bg: hsl(240 4.8% 95.9%);
      --bar-fill: hsl(200 29% 45%);
      --printer-led: hsl(142 50% 40%);
    }}
  }}

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    font-family: 'JetBrains Mono', monospace;
    background: var(--bg-body);
    color: var(--text-primary);
    line-height: 1.5;
    padding: 20px;
    display: flex;
    justify-content: center;
    min-height: 100vh;
    -webkit-font-smoothing: antialiased;
  }}

  .receipt-wrapper {{ position: relative; width: 400px; }}

  .receipt {{
    background: var(--bg-receipt);
    width: 400px;
    padding: 24px 20px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.4);
    position: relative;
    overflow: hidden;
    animation: printReceipt 2.5s ease-out forwards;
    transform-origin: top center;
    clip-path: inset(0 0 100% 0);
    border-radius: 2px;
  }}

  @keyframes printReceipt {{
    0% {{ clip-path: inset(0 0 100% 0); }}
    100% {{ clip-path: inset(0 0 0% 0); }}
  }}

  .receipt::before, .receipt::after {{
    content: '';
    position: absolute;
    left: 0; right: 0;
    height: 10px;
    background: radial-gradient(circle, transparent 6px, var(--bg-receipt) 6px);
    background-size: 16px 16px;
  }}
  .receipt::before {{ top: -5px; }}
  .receipt::after {{ bottom: -5px; transform: rotate(180deg); }}

  .printer-light {{
    position: absolute;
    top: -30px;
    left: 50%;
    transform: translateX(-50%);
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--printer-led);
    box-shadow: 0 0 8px var(--printer-led);
    animation: blink 0.5s ease-in-out 5;
  }}
  @keyframes blink {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.3; }} }}

  .header {{
    text-align: center;
    border-bottom: 2px dashed var(--border-dashed);
    padding-bottom: 16px;
    margin-bottom: 16px;
    opacity: 0;
    animation: fadeIn 0.3s ease forwards;
    animation-delay: 0.3s;
  }}
  .header .logo {{ font-size: 20px; font-weight: 700; letter-spacing: 4px; margin-bottom: 4px; color: var(--text-primary); }}
  .header .subtitle {{ font-size: 11px; color: var(--text-muted); letter-spacing: 2px; }}
  .header .date {{ font-size: 13px; font-weight: 600; margin-top: 8px; color: var(--accent); }}
  .header .joye {{ font-size: 10px; color: var(--text-muted); margin-top: 4px; letter-spacing: 1px; }}

  .section {{
    border-bottom: 1px dashed var(--border-dashed);
    padding: 12px 0;
    opacity: 0;
    animation: fadeIn 0.3s ease forwards;
  }}
  .section:nth-of-type(1) {{ animation-delay: 0.6s; }}
  .section:nth-of-type(2) {{ animation-delay: 0.9s; }}
  .section:nth-of-type(3) {{ animation-delay: 1.2s; }}
  .section:nth-of-type(4) {{ animation-delay: 1.5s; }}
  .section:nth-of-type(5) {{ animation-delay: 1.8s; }}
  .section:nth-of-type(6) {{ animation-delay: 2.1s; }}
  .section:nth-of-type(7) {{ animation-delay: 2.4s; }}
  .section:last-child {{ border-bottom: none; }}

  .section-title {{
    font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 2px;
    color: var(--text-muted); margin-bottom: 8px;
  }}

  .row {{ display: flex; justify-content: space-between; font-size: 12px; margin: 3px 0; }}
  .row .label {{ color: var(--text-secondary); }}
  .row .value {{ font-weight: 600; color: var(--text-primary); }}
  .row .highlight {{ font-weight: 700; font-size: 13px; color: var(--accent); }}

  .big-number {{ font-size: 28px; font-weight: 700; text-align: center; margin: 8px 0 4px; color: var(--text-primary); }}
  .big-label {{ font-size: 10px; text-align: center; color: var(--text-muted); text-transform: uppercase; letter-spacing: 2px; }}

  .token-grid {{
    display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin-top: 8px;
  }}
  .token-item {{
    text-align: center; padding: 8px 6px;
    background: var(--card-bg); border-radius: 4px; border: 1px solid var(--border);
  }}
  .token-item .num {{ font-size: 16px; font-weight: 700; color: var(--text-primary); }}
  .token-item .lbl {{ font-size: 9px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }}

  .model-bar {{ display: flex; align-items: center; margin: 4px 0; font-size: 11px; }}
  .model-name {{ width: 100px; font-weight: 600; color: var(--text-primary); }}
  .model-bar-fill {{ flex: 1; height: 14px; background: var(--bar-bg); border-radius: 2px; overflow: hidden; margin: 0 8px; }}
  .model-bar-inner {{ height: 100%; background: var(--bar-fill); border-radius: 2px; transition: width 1s ease; }}
  .model-count {{ width: 60px; text-align: right; font-size: 10px; color: var(--text-muted); }}

  .session-item {{ margin: 4px 0; font-size: 11px; }}
  .session-main {{ display: flex; justify-content: space-between; }}
  .session-time {{ font-weight: 600; color: var(--text-primary); }}
  .session-source {{ color: var(--text-muted); font-size: 10px; text-transform: uppercase; }}
  .session-title {{ color: var(--text-secondary); margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}

  .tool-name {{ font-weight: 600; color: var(--text-primary); }}
  .tool-count {{ color: var(--text-muted); font-size: 11px; }}

  .dash-line {{ border-top: 1px dashed var(--border-dashed); margin: 6px 0; }}

  .footer {{
    text-align: center; margin-top: 16px; padding-top: 12px;
    border-top: 2px dashed var(--border-dashed); font-size: 10px; color: var(--text-muted);
  }}
  .footer a {{ color: var(--text-secondary); text-decoration: none; }}
  .footer a:hover {{ color: var(--accent); }}

  .waka-main {{ text-align: center; margin: 8px 0; }}
  .waka-big {{ font-size: 24px; font-weight: 700; color: var(--accent); }}
  .waka-sublabel {{ font-size: 10px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; }}
  .waka-cats {{ margin-top: 8px; }}
  .waka-cat {{ display: flex; align-items: center; gap: 6px; font-size: 11px; margin: 3px 0; }}
  .waka-dot {{ width: 6px; height: 6px; border-radius: 50%; background: var(--accent); flex-shrink: 0; }}
  .waka-name {{ color: var(--text-secondary); flex: 1; }}
  .waka-val {{ color: var(--text-primary); font-weight: 600; }}

  @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(4px); }} to {{ opacity: 1; transform: translateY(0); }} }}

  @media (max-width: 440px) {{ .receipt, .receipt-wrapper {{ width: 100%; }} }}
</style>
</head>
<body>

<div class="receipt-wrapper">
  <div class="printer-light"></div>
  <div class="receipt">
    <div class="header">
      <div class="logo">HERMES AGENT</div>
      <div class="subtitle">DAILY RECEIPT</div>
      <div class="date">{display_date}</div>
      <div class="joye">joye @ joyehuang.me</div>
    </div>

    <div class="section">
      <div class="section-title">\u25a0 Overview</div>
      <div class="big-number">{session_count}</div>
      <div class="big-label">Sessions</div>
      <div class="token-grid">
        <div class="token-item">
          <div class="num">{total_msgs}</div>
          <div class="lbl">Messages</div>
        </div>
        <div class="token-item">
          <div class="num">{total_tools}</div>
          <div class="lbl">Tool Calls</div>
        </div>
        <div class="token-item">
          <div class="num">{total_fmt}</div>
          <div class="lbl">Total Tokens</div>
        </div>
      </div>
    </div>

{waka_section}

    <div class="section">
      <div class="section-title">\u25a0 Token Usage</div>
      <div class="row">
        <span class="label">Input Tokens</span>
        <span class="value highlight">{input_fmt}</span>
      </div>
      <div class="row">
        <span class="label">Output Tokens</span>
        <span class="value highlight">{output_fmt}</span>
      </div>
      <div class="row">
        <span class="label">Cache Read</span>
        <span class="value">{cache_r_fmt}</span>
      </div>
      <div class="row">
        <span class="label">Cache Write</span>
        <span class="value">{cache_w_fmt}</span>
      </div>
      <div class="row">
        <span class="label">Reasoning (est.)</span>
        <span class="value">{reason_fmt}</span>
      </div>
      <div class="dash-line"></div>
      <div class="row">
        <span class="label">TOTAL</span>
        <span class="value highlight">{total_fmt}</span>
      </div>
    </div>

    <div class="section">
      <div class="section-title">\u25a0 Models</div>
{model_rows}    </div>

    <div class="section">
      <div class="section-title">\u25a0 Platforms</div>
{platform_rows}    </div>

    <div class="section">
      <div class="section-title">\u25a0 Sessions</div>
{session_rows}    </div>

    <div class="section">
      <div class="section-title">\u25a0 Top Tools</div>
{tool_rows}    </div>

    <div class="footer">
      <div>Generated by Hermes Agent \u00b7 {date_str}</div>
      <div><a href="https://report.joyehuang.me">report.joyehuang.me</a></div>
    </div>
  </div>
</div>

<script>
(function() {{
  const ctx = new (window.AudioContext || window.webkitAudioContext)();
  const hum = ctx.createOscillator();
  hum.type = 'sine';
  hum.frequency.value = 60;
  const humGain = ctx.createGain();
  humGain.gain.setValueAtTime(0, ctx.currentTime);
  humGain.gain.linearRampToValueAtTime(0.06, ctx.currentTime + 0.3);
  humGain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 2.5);
  hum.connect(humGain);
  humGain.connect(ctx.destination);
  hum.start(ctx.currentTime);
  hum.stop(ctx.currentTime + 2.5);

  const clickTimes = [0.5, 0.65, 0.8, 0.95, 1.1, 1.25, 1.4, 1.55, 1.7, 1.85, 2.0, 2.15];
  clickTimes.forEach(t => {{
    const bufSize = ctx.sampleRate * 0.025;
    const buf = ctx.createBuffer(1, bufSize, ctx.sampleRate);
    const data = buf.getChannelData(0);
    for (let i = 0; i < bufSize; i++) data[i] = Math.random() * 2 - 1;
    const noise = ctx.createBufferSource();
    noise.buffer = buf;
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.12, ctx.currentTime + t);
    g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + t + 0.025);
    noise.connect(g);
    g.connect(ctx.destination);
    noise.start(ctx.currentTime + t);
  }});

  const tearSize = ctx.sampleRate * 0.12;
  const tearBuf = ctx.createBuffer(1, tearSize, ctx.sampleRate);
  const tearData = tearBuf.getChannelData(0);
  for (let i = 0; i < tearSize; i++) tearData[i] = (Math.random() * 2 - 1) * (1 - i / tearSize);
  const tear = ctx.createBufferSource();
  tear.buffer = tearBuf;
  const tearGain = ctx.createGain();
  tearGain.gain.setValueAtTime(0.08, ctx.currentTime + 2.3);
  tearGain.gain.linearRampToValueAtTime(0, ctx.currentTime + 2.5);
  tear.connect(tearGain);
  tearGain.connect(ctx.destination);
  tear.start(ctx.currentTime + 2.3);
}})();
</script>

</body>
</html>"""
