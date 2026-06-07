import requests
import re
import time

ids = ["2606.05296","2606.05885","2606.06058","2606.05263","2606.05434","2606.05784","2606.05800","2606.05523","2606.05174"]

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
                print(f"\n=== {arxiv_id} ===")
                print(f"Title: {title}")
                print(f"Summary: {summary}")
        time.sleep(2)
    except Exception as ex:
        print(f"Error: {ex}")
