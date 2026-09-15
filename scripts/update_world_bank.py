import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

OUT = Path(__file__).parents[1] / "data/opportunities.json"
URL = "https://datacatalogapi.worldbank.org/dexapps/fone/api/apiservice"
BASE = {"datasetId": "DS00979", "resourceId": "RS00909", "type": "json"}
SCAN_ROWS = 4000
MAX_ROWS = 400


def iso_date(value):
    if not value:
        return ""
    value = str(value).strip()
    for pattern in ("%d-%b-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value[:11], pattern).date().isoformat()
        except ValueError:
            pass
    return ""


def normalize(item, today):
    title = str(item.get("bid_description") or "").strip()
    notice_type = str(item.get("notice_type") or "Procurement notice").strip()
    deadline = iso_date(item.get("deadline_date"))
    published = iso_date(item.get("publication_date"))
    if not title or item.get("id") in (None, ""):
        return None
    if notice_type.casefold() in {"contract award", "general procurement notice", "procurement plan"}:
        return None
    if deadline and deadline < today.isoformat():
        return None
    if not deadline and published and published < (today - timedelta(days=45)).isoformat():
        return None
    return {
        "source": "World Bank",
        "source_id": f"WB-{item['id']}",
        "title": title,
        "organization": "World Bank",
        "office": "",
        "country": item.get("country_name") or item.get("region") or "",
        "state": "",
        "notice_type": notice_type,
        "naics": "",
        "solicitation_number": str(item.get("project_id") or ""),
        "deadline": deadline,
        "published": published,
        "contacts": [],
        "description": " • ".join(filter(None, [str(item.get("procurement_method") or ""), str(item.get("procurement_category") or "")])),
        "url": item.get("url") or "https://projects.worldbank.org/en/projects-operations/procurement",
    }


def main():
    first = requests.get(URL, params={**BASE, "skip": 0, "top": 1}, timeout=90)
    first.raise_for_status()
    count = int(first.json()["count"])
    start = max(0, count - SCAN_ROWS)
    raw = []
    for skip in range(start, count, 1000):
        response = requests.get(URL, params={**BASE, "skip": skip, "top": min(1000, count - skip)}, timeout=90)
        response.raise_for_status()
        raw.extend(response.json().get("data", []))
    today = datetime.now(timezone.utc).date()
    rows = [row for row in (normalize(item, today) for item in raw) if row]
    rows.sort(key=lambda row: (row["published"], row["deadline"]), reverse=True)
    unique = {row["source_id"]: row for row in rows}
    world_bank = list(unique.values())[:MAX_ROWS]
    existing = json.loads(OUT.read_text()) if OUT.exists() else []
    combined = [row for row in existing if row.get("source") != "World Bank"] + world_bank
    OUT.write_text(json.dumps(combined, indent=2, ensure_ascii=False) + "\n")
    print(f"World Bank open opportunities: {len(world_bank)}")


if __name__ == "__main__":
    main()
