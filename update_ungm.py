import json,os,requests
from pathlib import Path
OUT=Path(__file__).parents[1]/"data/opportunities.json"
TOKEN=os.getenv("UNGM_ACCESS_TOKEN")
if not TOKEN:
 print("UNGM_ACCESS_TOKEN not set; skipping UNGM. Add it later as a GitHub Actions secret.")
 raise SystemExit
url="https://www.ungm.org/API/Notices"
headers={"Accept":"application/json","Authorization":"bearer "+TOKEN}
r=requests.get(url,headers=headers,timeout=45); r.raise_for_status(); p=r.json()
raw=p.get("value",[])
rows=json.loads(OUT.read_text()) if OUT.exists() else []
d={str(x.get("source_id")):x for x in rows if x.get("source_id")}
for x in raw:
 sid="UNGM-"+str(x.get("Id"))
 d[sid]={**d.get(sid,{}),"source":"UNGM","source_id":sid,"title":x.get("Title",""),"organization":x.get("AgencyName") or x.get("Agency") or "UNGM","country":x.get("CountryName") or "","notice_type":x.get("Type",""),"deadline":x.get("Deadline") or "","published":x.get("DatePublished") or "","url":"https://www.ungm.org/Public/Notice/"+str(x.get("Id"))}
OUT.write_text(json.dumps(list(d.values()),indent=2,ensure_ascii=False))
print("UNGM records:",sum(1 for x in d.values() if x.get("source")=="UNGM"))
