import json,re
from pathlib import Path
P=Path(__file__).parents[1]/"data/opportunities.json"
CAP={"security":10,"national security":10,"defense":10,"defence":10,"maritime":10,"logistics":8,"training":7,"governance":7,"strategic communications":8,"human rights":8,"osint":8,"supply chain":9,"responsible sourcing":9,"disaster":6,"resilience":6}
GEO={"australia":15,"papua new guinea":15,"fiji":15,"solomon islands":15,"vanuatu":15,"marshall islands":15,"micronesia":15,"palau":15,"indonesia":12,"philippines":12,"timor-leste":12}
def main():
 rows=json.loads(P.read_text())
 for x in rows:
  t=" ".join(str(x.get(k,"")) for k in ("title","project","notice_type","procurement_method")).lower()
  cap=min(30,sum(v for k,v in CAP.items() if k in t)); geo=GEO.get(str(x.get("country","")).lower(),5)
  strategic=10 if any(k in t for k in ("security","maritime","governance","human rights","supply chain")) else 4
  score=min(100,cap+geo+10+strategic)
  x["score"]=score; x["recommendation"]="PURSUE" if score>=80 else "INVESTIGATE" if score>=65 else "WATCH" if score>=45 else "PASS"
  x["fit_reason"]="Initial transparent rules-based score; capability and geography matches are emphasized."
 rows.sort(key=lambda x:x.get("score",0),reverse=True); P.write_text(json.dumps(rows,indent=2,ensure_ascii=False))
if __name__=="__main__": main()
