"""Fetch live USD/CNY and USD/AUD exchange rates and update cost_tracker.py."""

import re
import urllib.request
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COST_TRACKER = os.path.join(SCRIPT_DIR, "cost_tracker.py")


def fetch_rate(pair: str) -> float:
    """Fetch rate from xe.com. pair e.g. 'USDCNY' or 'USDAUD'."""
    url = f"https://www.xe.com/currencyconverter/convert/?From=USD&To={pair[3:]}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0"
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode()

    # Look for pattern like: 1 USD = 6.83 CNY or 1.00 USD = 6.83058287 CNY
    m = re.search(r'1\.?\d*\s*USD\s*=\s*([\d.]+)\s*' + pair[3:], html, re.IGNORECASE)
    if m:
        rate = float(m.group(1))
        # For AUD: rate = how many AUD per USD, we need USD per AUD = 1/rate
        # For CNY: rate = how many CNY per USD, we need USD per CNY = 1/rate
        return round(1.0 / rate, 4)
    
    # Fallback: parse the conversion table
    # USD to CNY table: 1 USD = 6.83058 CNY
    m = re.search(r'1\s*USD\s*=\s*([\d.]+)\s*' + pair[3:], html)
    if m:
        rate = float(m.group(1))
        return round(1.0 / rate, 4)
    
    raise ValueError(f"Could not parse rate for {pair}")


def update_rates(cny_rate: float, aud_rate: float):
    """Update the rates dict in cost_tracker.py."""
    with open(COST_TRACKER, "r") as f:
        content = f.read()

    old_line = re.search(r'rates\s*=\s*\{[^}]+\}', content)
    if not old_line:
        raise ValueError("Could not find rates dict in cost_tracker.py")

    new_line = f'rates = {{"USD": 1.0, "CNY": {cny_rate}, "AUD": {aud_rate}}}'
    content = content.replace(old_line.group(0), new_line)

    with open(COST_TRACKER, "w") as f:
        f.write(content)


def main():
    print("🌐 Fetching live exchange rates...")
    
    cny_rate = fetch_rate("USDCNY")
    aud_rate = fetch_rate("USDAUD")
    
    print(f"  1 CNY = {cny_rate} USD")
    print(f"  1 AUD = {aud_rate} USD")
    
    old_cny = None
    old_aud = None
    with open(COST_TRACKER) as f:
        m = re.search(r'rates\s*=\s*\{[^}]+\}', f.read())
        if m:
            old = m.group(0)
            cny_m = re.search(r'CNY:\s*([\d.]+)', old)
            aud_m = re.search(r'AUD:\s*([\d.]+)', old)
            if cny_m: old_cny = float(cny_m.group(1))
            if aud_m: old_aud = float(aud_m.group(1))
    
    if old_cny:
        print(f"  Previous: 1 CNY = {old_cny} USD (change: {cny_rate - old_cny:+.4f})")
    if old_aud:
        print(f"  Previous: 1 AUD = {old_aud} USD (change: {aud_rate - old_aud:+.4f})")
    
    update_rates(cny_rate, aud_rate)
    print(f"\n✅ Updated cost_tracker.py")
    print(f"   rates = {{\"USD\": 1.0, \"CNY\": {cny_rate}, \"AUD\": {aud_rate}}}")


if __name__ == "__main__":
    main()
