import requests
import time
import re

with open('all_ids.txt') as f:
    all_ids = [line.strip() for line in f if line.strip()]

keywords = [
    "agentic","grpo","rlvr","reinforcement learning","tool use","tool-use",
    "multi-agent","multi agent","code agent","ppo","policy optimization",
    "verifiable reward","sparse reward","rollout","advantage","credit",
    "long horizon","long-horizon","reasoning agent","agent training","mappo","marl",
    "search agent","black-box agent","rubric reward","adversarial", "tapo", "asyncwebrl",
    "ecpo", "hpo", "salt", "cero", "mdp-grpo", "amc", "cvt-rl", "monte carlo",
    "group relative", "group-relative", "black box agent"
]

results = []
for i in range(0, len(all_ids), 100):
    batch = all_ids[i:i+100]
    query = ",".join(batch)
    url = f"http://export.arxiv.org/api/query?id_list={query}"
    try:
        r = requests.get(url, timeout=60)
        entries = re.findall(r'<entry>(.*?)</entry>', r.text, re.DOTALL)
        for e in entries:
            id_match = re.search(r'<id>http://arxiv.org/abs/([\d.]+)', e)
            title_match = re.search(r'<title>(.*?)</title>', e, re.DOTALL)
            summary_match = re.search(r'<summary>(.*?)</summary>', e, re.DOTALL)
            cat_match = re.search(r'<arxiv:primary_category term="(.*?)"', e)
            if id_match and title_match:
                arxiv_id = id_match.group(1)
                title = re.sub(r'\s+', ' ', title_match.group(1)).strip()
                summary = re.sub(r'\s+', ' ', summary_match.group(1)).strip() if summary_match else ""
                cat = cat_match.group(1) if cat_match else ""
                text = (title + " " + summary).lower()
                score = sum(1 for k in keywords if k in text)
                # Boosting
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
                if score >= 3:
                    results.append((arxiv_id, title, summary, cat, score))
        print(f"Batch {i//100+1}/{(len(all_ids)-1)//100+1}: {len(results)} total matches so far")
        time.sleep(5)
    except Exception as ex:
        print(f"Error batch {i//100+1}: {ex}")

results.sort(key=lambda x: x[4], reverse=True)
print(f"\nTotal matched: {len(results)}")
for r in results[:30]:
    print(f"\nID: {r[0]} | Score: {r[4]} | Cat: {r[3]}")
    print(f"Title: {r[1]}")
    print(f"Summary: {r[2][:400]}...")
