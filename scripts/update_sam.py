import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

OUT = Path(__file__).parents[1] / "data/opportunities.json"
URL = "https://api.sam.gov/opportunities/v2/search"

# Search separately for high-confidence SWAT/tactical terms and adjacent
# training signals. SAM searches federal contract opportunities, so this is
# deliberately broader than just the word SWAT.
QUERIES = [
    # Direct SWAT / special operations
    "SWAT",
    "SWAT training",
    "SWAT instructor",
    "special weapons and tactics",
    "special operations training",
    "tactical team training",
    "tactical training",
    "hostage rescue",
    "CQB",
    "close quarters combat",
    "breaching training",
    "breacher training",
    # Tactical training methods
    "force on force",
    "force-on-force",
    "Simunition",
    "UTM training",
    "scenario based training",
    "scenario-based training",
    "tactical firearms",
    "firearms instructor",
    "tactical medical",
    "tactical medicine",
    "active shooter training",
    "crisis response training",
    # Facilities / precursor buying signals
    "SWAT facility",
    "tactical training facility",
    "shoot house",
    "shooting house",
    "kill house",
    "tactical training tower",
    "training tower",
    # Broader law-enforcement training terms
    "police training",
    "law enforcement training",
    "law enforcement instructor",
]


def text(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def first(*values):
    for value in values:
        if value not in (None, "", []):
            return value
    return ""


def extract_records(payload):
    for key in ("opportunitiesData", "opportunities", "results", "documents"):
        value = payload.get(key) if isinstance(payload, dict) else None
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            for nested in ("opportunity", "items", "data"):
                if isinstance(value.get(nested), list):
                    return value[nested]
    return []


def normalize(item):
    poc = item.get("pointOfContact") or item.get("pointOfContactList") or []
    if isinstance(poc, dict):
        poc = [poc]
    contacts = []
    for p in poc[:5]:
        name = first(p.get("fullName"), p.get("name"))
        email = first(p.get("email"), p.get("emailAddress"))
        phone = first(p.get("phone"), p.get("phoneNumber"))
        if name or email or phone:
            contacts.append({"name": name, "email": email, "phone": phone})

    org = first(
        item.get("organizationType"),
        item.get("organization"),
        item.get("department"),
        item.get("agencyName"),
    )
    office = first(item.get("subTier"), item.get("office"), item.get("contractingOfficeName"))
    title = first(item.get("title"), item.get("solicitationTitle"), item.get("description"), "SAM.gov opportunity")
    notice_id = first(item.get("noticeId"), item.get("solicitationNumber"), item.get("id"))
    url = first(
        item.get("uiLink"),
        item.get("link"),
        item.get("url"),
        f"https://sam.gov/opp/{notice_id}/view" if notice_id else "https://sam.gov/content/opportunities",
    )

    return {
        "source": "SAM.gov",
        "source_id": text(notice_id),
        "title": text(title),
        "organization": text(org),
        "office": text(office),
        "country": "United States",
        "state": text(first(item.get("placeOfPerformance"), item.get("state"), item.get("placeOfPerformanceState"))),
        "notice_type": text(first(item.get("type"), item.get("noticeType"), item.get("baseType"))),
        "naics": text(first(item.get("naicsCode"), item.get("naics"))),
        "solicitation_number": text(first(item.get("solicitationNumber"), item.get("solicitationId"))),
        "deadline": text(first(item.get("responseDeadLine"), item.get("responseDeadline"), item.get("deadline"))),
        "published": text(first(item.get("postedDate"), item.get("publicationDate"), item.get("modifiedDate"))),
        "contacts": contacts,
        "description": text(first(item.get("description"), item.get("additionalInfo"))),
        "url": text(url),
        "sam_query": "",
    }


def main():
    api_key = os.environ.get("SAM_API_KEY")
    if not api_key:
        raise RuntimeError("SAM_API_KEY is not set. Add it as a GitHub Actions secret named SAM_API_KEY.")

    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=90)
    posted_from = start.strftime("%m/%d/%Y")
    posted_to = end.strftime("%m/%d/%Y")

    records = {}
    for query in QUERIES:
        offset = 0
        while True:
            params = {
                "api_key": api_key,
                "q": query,
                "postedFrom": posted_from,
                "postedTo": posted_to,
                "limit": 100,
                "offset": offset,
            }
            response = requests.get(URL, params=params, timeout=60)
            response.raise_for_status()
            payload = response.json()
            items = extract_records(payload)
            if not items:
                break

            for item in items:
                row = normalize(item)
                if not row["source_id"]:
                    continue
                existing = records.get(row["source_id"])
                if existing:
                    queries = set(existing.get("sam_queries", []))
                    queries.add(query)
                    existing["sam_queries"] = sorted(queries)
                    records[row["source_id"]] = existing
                else:
                    row["sam_queries"] = [query]
                    records[row["source_id"]] = row

            if len(items) < 100:
                break
            offset += 100

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(list(records.values()), indent=2, ensure_ascii=False))
    print(f"SAM.gov SWAT/tactical opportunities: {len(records)}")


if __name__ == "__main__":
    main()
