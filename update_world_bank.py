import json,requests
from pathlib import Path
OUT=Path(__file__).parents[1]/"data/opportunities.json"
URL="https://search.worldbank.org/api/v2/procnotices?format=json&fl=id,submission_deadline_date,project_ctry_name,project_id,project_name,notice_type,notice_type_name,procurement_group,procurement_method,notice_description,publication_date,project_url&srt=publication_date&order=desc&os=0&rows=100"
def main():
 r=requests.get(URL,timeout=45); r.raise_for_status(); p=r.json()
 raw=p.get("procnotices") or p.get("documents") or p.get("results") or []
 if isinstance(raw,dict): raw=raw.get("document",raw.get("items",[]))
 old=json.loads(OUT.read_text()) if OUT.exists() else []
 d={str(x.get("source_id")):x for x in old if x.get("source_id")}
 for x in raw:
  sid=str(x.get("id") or x.get("procurement_notice_id") or "")
  if not sid: continue
  d[sid]={
   **d.get(sid,{}),
   "source":"World Bank","source_id":sid,
   "title":x.get("notice_description") or x.get("project_name") or "World Bank procurement notice",
   "organization":"World Bank","country":x.get("project_ctry_name") or "",
   "project":x.get("project_name") or "","project_id":x.get("project_id") or "",
   "notice_type":x.get("notice_type_name") or x.get("notice_type") or "",
   "procurement_method":x.get("procurement_method") or "",
   "deadline":x.get("submission_deadline_date") or "",
   "published":x.get("publication_date") or "",
   "url":x.get("project_url") or "https://projects.worldbank.org/",
  }
 OUT.write_text(json.dumps(list(d.values()),indent=2,ensure_ascii=False))
 print("World Bank records:",len(d))
if __name__=="__main__": main()
