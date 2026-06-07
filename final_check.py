import requests
import re

ids = ["2606.05296","2606.05263","2606.05784","2606.05885","2606.05800"]
url = f"http://export.arxiv.org/api/query?id_list={','.join(ids)}"
r = requests.get(url, timeout=30)
entries = re.findall(r'<entry>(.*?)</entry>', r.text, re.DOTALL)
for e in entries:
    id_match = re.search(r'<id>http://arxiv.org/abs/([\d.]+)', e)
    title_match = re.search(r'<title>(.*?)</title>', e, re.DOTALL)
    date_match = re.search(r'<published>(.*?)</published>', e)
    if id_match and title_match:
        title_clean = re.sub(r'\s+', ' ', title_match.group(1)).strip()
        date_str = date_match.group(1)[:10] if date_match else 'N/A'
        print(f"{id_match.group(1)} | {date_str} | {title_clean}")
