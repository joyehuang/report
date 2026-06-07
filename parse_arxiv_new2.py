import re
import requests

headers = {'User-Agent': 'Mozilla/5.0'}

def fetch_new_submissions(cat):
    url = f"https://arxiv.org/list/{cat}/new"
    r = requests.get(url, headers=headers, timeout=30)
    text = r.text
    # Find the New submissions section
    m = re.search(r'<h3>New submissions.*?</h3>(.*?)<h3>Cross submissions', text, re.DOTALL)
    if not m:
        return []
    section = m.group(1)
    # Extract IDs and titles
    pattern = r'<a href ="/abs/([\d.]+)"[^>]*>.*?<div class=\'list-title mathjax\'><span class=\'descriptor\'>Title:</span>(.*?)</div>'
    matches = re.findall(pattern, section, re.DOTALL)
    results = []
    for m in matches:
        arxiv_id = m[0]
        title = re.sub(r'<[^>]+>', '', m[1]).strip()
        results.append((arxiv_id, title))
    return results

keywords = [
    "agentic","grpo","rlvr","reinforcement learning","tool use","tool-use",
    "multi-agent","multi agent","code agent","ppo","policy optimization",
    "verifiable reward","sparse reward","rollout","advantage","credit",
    "long horizon","long-horizon","reasoning agent","agent training","mappo","marl",
    "search agent","black-box agent","rubric reward","adversarial", "tapo", "asyncwebrl",
    "ecpo", "hpo", "salt", "cero", "mdp-grpo", "amc", "cvt-rl", "monte carlo",
    "group relative", "group-relative", "black box agent"
]

all_results = []
for cat in ['cs.AI','cs.LG','cs.CL']:
    items = fetch_new_submissions(cat)
    print(f"{cat} new submissions: {len(items)} items")
    for item in items:
        arxiv_id, title = item
        text = title.lower()
        score = sum(1 for k in keywords if k in text)
        if "agentic" in text and ("reinforcement learning" in text or "rl" in title.lower() or "policy" in text or "grpo" in text):
            score += 3
        if "grpo" in text:
            score += 2
        if "tool" in text and "reinforcement" in text:
            score += 2
        if "multi-agent" in text and "reinforcement" in text:
            score += 2
        if "long-horizon" in text and "agent" in text:
            score += 2
        if "verifiable" in text and "reward" in text and "agent" in text:
            score += 2
        if "black-box" in text and "agent" in text and ("rl" in text or "reinforcement" in text or "monte carlo" in text):
            score += 3
        if score >= 2:
            all_results.append((arxiv_id, title, cat, score))

all_results.sort(key=lambda x: x[3], reverse=True)
print(f"\nTotal matched: {len(all_results)}")
for r in all_results:
    print(f"ID: {r[0]} | Score: {r[3]} | Cat: {r[2]} | {r[1]}")
