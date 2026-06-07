import requests
import xml.etree.ElementTree as ET
import re

ns = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}

keywords = [
    "agentic","grpo","rlvr","reinforcement learning","tool use","tool-use",
    "multi-agent","multi agent","code agent","ppo","policy optimization",
    "verifiable reward","sparse reward","rollout","advantage","credit",
    "long horizon","long-horizon","reasoning agent","agent training","mappo","marl",
    "search agent","black-box agent","rubric reward","adversarial", "tapo", "asyncwebrl",
    "ecpo", "hpo", "salt", "cero", "mdp-grpo", "amc", "cvt-rl"
]

all_entries = []
for cat in ['cs.AI','cs.LG','cs.CL']:
    url = f"http://export.arxiv.org/api/query?search_query=cat:{cat}&sortBy=submittedDate&sortOrder=descending&max_results=200"
    try:
        r = requests.get(url, timeout=60)
        root = ET.fromstring(r.content)
        entries = root.findall('atom:entry', ns)
        for entry in entries:
            id_elem = entry.find('atom:id', ns)
            title_elem = entry.find('atom:title', ns)
            summary_elem = entry.find('atom:summary', ns)
            date_elem = entry.find('atom:published', ns)
            cat_elem = entry.find('arxiv:primary_category', ns)
            if id_elem is None or title_elem is None:
                continue
            arxiv_id = id_elem.text.split('/')[-1].replace('v1','').replace('v2','')
            title = re.sub(r'\s+', ' ', title_elem.text).strip()
            summary = re.sub(r'\s+', ' ', summary_elem.text).strip() if summary_elem is not None else ""
            date = date_elem.text[:10] if date_elem is not None else ""
            category = cat_elem.get('term') if cat_elem is not None else cat
            # Only keep June 5-6, 2026
            if date not in ['2026-06-05','2026-06-06']:
                continue
            text = (title + " " + summary).lower()
            score = sum(1 for k in keywords if k in text)
            # Boost specific core terms
            if "agentic" in text and ("reinforcement learning" in text or "rl" in title.lower() or "policy" in text or "grpo" in text):
                score += 3
            if "grpo" in text:
                score += 2
            if "tool" in text and "reinforcement" in text:
                score += 2
            if "multi-agent" in text and "reinforcement" in text:
                score += 2
            if score >= 2:
                all_entries.append((arxiv_id, title, summary, date, category, score))
    except Exception as ex:
        print(f"Error for {cat}: {ex}")

# Deduplicate by ID
seen = set()
unique_entries = []
for e in all_entries:
    if e[0] not in seen:
        seen.add(e[0])
        unique_entries.append(e)

unique_entries.sort(key=lambda x: x[5], reverse=True)

print(f"Total matched: {len(unique_entries)}")
for e in unique_entries[:25]:
    print(f"\nID: {e[0]} | Date: {e[3]} | Cat: {e[4]} | Score: {e[5]}")
    print(f"Title: {e[1]}")
    print(f"Summary: {e[2][:380]}...")
