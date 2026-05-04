# Joye's Daily Report

**Live URL:** https://report.joyehuang.me

Automated daily activity report generated from Hermes Agent usage + WakaTime coding data.

## Structure

```
├── generate_receipt.py      # Main script (cron runs this)
├── generate_dashboard.py    # AI Overview dashboard (future)
├── agent.sh                 # Auto git commit + push helper
├── lib/
│   ├── wakatime.py          # WakaTime API client
│   ├── hermes_db.py         # Hermes state.db queries
│   └── template.py          # HTML receipt renderer
├── assets/
│   └── ai-overview-demo.html  # AI Overview design demo
├── archive/
│   └── joye-receipt-YYYY-MM-DD.html
└── index.html               # Landing page
```

## Cron

Runs daily at 08:00 Melbourne time via Hermes cron job.

## Agent Script

```bash
./agent.sh "optional commit message"
```

Auto-commits and pushes any changes.
