import re
import requests

headers = {'User-Agent': 'Mozilla/5.0'}

def fetch_new_submissions(cat):
    url = f"https://arxiv.org/list/{cat}/new"
    r = requests.get(url, headers=headers, timeout=30)
    text = r.text
    # Split into sections: New submissions, Cross lists, Replacements
    sections = re.split(r'<h3>.*?</h3>', text)
    # Usually sections[1] is New submissions
    new_section = sections[1] if len(sections) > 1 else text
    # Extract IDs and titles from new section
    pattern = r'<a href ="/abs/([\d.]+)"[^>]*>.*?<div class=\'list-title mathjax\'><span class=\'descriptor\'>Title:</span>(.*?)</div>'
    matches = re.findall(pattern, new_section, re.DOTALL)
    results = []
    for m in matches:
        arxiv_id = m[0]
        title = re.sub(r'<[^>]+>', '', m[1]).strip()
        # Extract abstract - try to find the abstract following this entry
        abs_pattern = f'<a href ="/abs/{arxiv_id}"[^>]*>.*?</p>\\s*<p class="mathjax">(.*?)</p>'
        abs_match = re.search(abs_pattern, new_section, re.DOTALL)
        abstract = ""
        if abs_match:
            abstract = re.sub(r'<[^>]+>', '', abs_match.group(1)).strip()
        results.append((arxiv_id, title, abstract))
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
        arxiv_id, title, abstract = item
        text = (title + " " + abstract).lower()
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
            all_results.append((arxiv_id, title, abstract, cat, score))

# Deduplicate
seen = set()
unique_results = []
for r in all_results:
    if r[0] not in seen:
        seen.add(r[0])
        unique_results.append(r)

unique_results.sort(key=lambda x: x[4], reverse=True)
print(f"\nTotal unique matched: {len(unique_results)}")
for r in unique_results[:30]:
    print(f"\nID: {r[0]} | Score: {r[4]} | Cat: {r[3]}")
    print(f"Title: {r[1]}")
    print(f"Abstract: {r[2][:450]}...")
