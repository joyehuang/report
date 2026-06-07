import requests
import time
import re

# IDs from cs.AI new submissions page (June 5, 2026)
ai_ids = [
"2606.05256","2606.05304","2606.05316","2606.05332","2606.05334","2606.05342",
"2606.05357","2606.05382","2606.05384","2606.05389","2606.05400","2606.05404",
"2606.05405","2606.05408","2606.05411","2606.05420","2606.05429","2606.05433",
"2606.05436","2606.05445","2606.05449","2606.05461","2606.05463","2606.05464",
"2606.05510","2606.05513","2606.05525","2606.05528","2606.05532","2606.05563"
]

# IDs from cs.LG new submissions page
lg_ids = [
"2606.05169","2606.05170","2606.05186","2606.05191","2606.05194","2606.05201",
"2606.05219","2606.05232","2606.05247","2606.05253","2606.05254","2606.05257",
"2606.05263","2606.05264","2606.05265","2606.05266","2606.05272","2606.05274",
"2606.05296","2606.05308","2606.05327","2606.05335","2606.05345","2606.05371",
"2606.05373","2606.05376","2606.05378","2606.05381","2606.05403","2606.05413"
]

# IDs from cs.CL new submissions page
cl_ids = [
"2606.05168","2606.05173","2606.05174","2606.05175","2606.05176","2606.05177",
"2606.05179","2606.05180","2606.05181","2606.05182","2606.05183","2606.05315",
"2606.05330","2606.05336","2606.05346","2606.05402","2606.05414","2606.05415",
"2606.05421","2606.05444","2606.05486","2606.05494","2606.05523","2606.05545",
"2606.05553","2606.05557","2606.05561","2606.05564","2606.05569","2606.05570"
]

all_ids = list(set(ai_ids + lg_ids + cl_ids))

keywords = [
    "agentic","grpo","rlvr","reinforcement learning","tool use","tool-use",
    "multi-agent","multi agent","code agent","ppo","policy optimization",
    "verifiable reward","sparse reward","rollout","advantage","credit",
    "long horizon","long-horizon","reasoning agent","agent training","mappo","marl",
    "search agent","black-box agent","rubric reward","adversarial", "tapo", "asyncwebrl",
    "ecpo", "hpo", "salt", "cero", "mdp-grpo", "amc", "cvt-rl", "monte carlo"
]

results = []
for i in range(0, len(all_ids), 10):
    batch = all_ids[i:i+10]
    query = ",".join(batch)
    url = f"http://export.arxiv.org/api/query?id_list={query}"
    try:
        r = requests.get(url, timeout=30)
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
                # Boost
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
                if score >= 3:
                    results.append((arxiv_id, title, summary, cat, score))
        time.sleep(3)
    except Exception as ex:
        print(f"Error: {ex}")

results.sort(key=lambda x: x[4], reverse=True)
print(f"Total matched: {len(results)}")
for r in results[:20]:
    print(f"\nID: {r[0]} | Score: {r[4]} | Cat: {r[3]}")
    print(f"Title: {r[1]}")
    print(f"Summary: {r[2][:400]}...")
