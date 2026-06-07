import requests
import re
import time

# Fetch specific IDs I want to check
ids = ["2606.05304","2606.05201","2606.05327","2606.05403","2606.05194","2606.05232","2606.05247","2606.05254","2606.05257","2606.05264","2606.05266","2606.05272","2606.05274","2606.05308","2606.05335","2606.05345","2606.05371","2606.05373","2606.05376","2606.05378","2606.05381","2606.05413","2606.05414","2606.05415","2606.05421","2606.05444","2606.05486","2606.05494","2606.05525","2606.05528","2606.05532","2606.05545","2606.05553","2606.05557","2606.05561","2606.05564","2606.05569","2606.05570","2606.05400","2606.05405","2606.05408","2606.05411","2606.05420","2606.05429","2606.05433","2606.05436","2606.05445","2606.05449","2606.05461","2606.05463","2606.05464","2606.05510","2606.05513"]

for i in range(0, len(ids), 10):
    batch = ids[i:i+10]
    query = ",".join(batch)
    url = f"http://export.arxiv.org/api/query?id_list={query}"
    try:
        r = requests.get(url, timeout=30)
        entries = re.findall(r'<entry>(.*?)</entry>', r.text, re.DOTALL)
        for e in entries:
            id_match = re.search(r'<id>http://arxiv.org/abs/([\d.]+)', e)
            title_match = re.search(r'<title>(.*?)</title>', e, re.DOTALL)
            summary_match = re.search(r'<summary>(.*?)</summary>', e, re.DOTALL)
            if id_match and title_match:
                arxiv_id = id_match.group(1)
                title = re.sub(r'\s+', ' ', title_match.group(1)).strip()
                summary = re.sub(r'\s+', ' ', summary_match.group(1)).strip() if summary_match else ""
                # Only print if relevant
                text = (title + " " + summary).lower()
                if any(k in text for k in ["agentic","grpo","rlvr","reinforcement learning","tool use","tool-use","multi-agent","code agent","ppo","policy optimization","verifiable reward","sparse reward","rollout","advantage","credit","long horizon","long-horizon","reasoning agent","agent training","marl","search agent","black-box agent","rubric reward","adversarial","monte carlo"]):
                    print(f"\n=== {arxiv_id} ===")
                    print(f"Title: {title}")
                    print(f"Summary: {summary[:500]}...")
        time.sleep(2)
    except Exception as ex:
        print(f"Error: {ex}")
