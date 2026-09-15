import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

OUT = Path(__file__).parents[1] / "data/opportunities.json"
URL = "https://api.sam.gov/opportunities/v2/search"
PAGE_SIZE = 1000
MAX_PAGES = 25


def text(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def first(*values):
    return next((value for value in values if value not in (None, "", [])), "")


def iso_date(value):
    value = text(value).strip()
    return value[:10] if len(value) >= 10 else value


def extract_records(payload):
    value = payload.get("opportunitiesData", []) if isinstance(payload, dict) else []
    return value if isinstance(value, list) else []


def normalize(item, today):
    notice_id = first(item.get("noticeId"), item.get("solicitationNumber"), item.get("id"))
    notice_type = text(first(item.get("type"), item.get("baseType"), "Procurement notice"))
    deadline = iso_date(first(item.get("responseDeadLine"), item.get("responseDeadline")))
    active = text(item.get("active")).casefold()
    if not notice_id or notice_type.casefold() in {
        "award notice", "justification", "sale of surplus property"
    }:
        return None
    if active in {"no", "false", "inactive", "archived"}:
        return None
    if deadline and deadline < today.isoformat():
        return None
    poc = item.get("pointOfContact") or []
    if isinstance(poc, dict):
        poc = [poc]
    contacts = []
    for person in poc[:5]:
        contact = {
            "name": first(person.get("fullName"), person.get("name")),
            "email": first(person.get("email"), person.get("emailAddress")),
            "phone": first(person.get("phone"), person.get("phoneNumber")),
        }
        if any(contact.values()):
            contacts.append(contact)
    performance = item.get("placeOfPerformance") or {}
    state = performance.get("state") if isinstance(performance, dict) else ""
    if isinstance(state, dict):
        state = first(state.get("name"), state.get("code"))
    title = first(item.get("title"), item.get("solicitationTitle"), "SAM.gov opportunity")
    return {
        "source": "SAM.gov",
        "source_id": text(notice_id),
        "title": text(title),
        "organization": text(first(item.get("fullParentPathName"), item.get("department"), "U.S. government")),
        "office": text(first(item.get("subTier"), item.get("office"))),
        "country": "United States",
        "state": text(state),
        "notice_type": notice_type,
        "naics": text(item.get("naicsCode")),
        "solicitation_number": text(item.get("solicitationNumber")),
        "deadline": deadline,
        "published": iso_date(item.get("postedDate")),
        "contacts": contacts,
        "description": "",
        "url": text(first(item.get("uiLink"), f"https://sam.gov/opp/{notice_id}/view")),
    }


def fetch_sam(api_key, today):
    params = {
        "api_key": api_key,
        "postedFrom": (today - timedelta(days=90)).strftime("%m/%d/%Y"),
        "postedTo": today.strftime("%m/%d/%Y"),
        "limit": PAGE_SIZE,
    }
    records = {}
    offset = 0
    for _ in range(MAX_PAGES):
        response = requests.get(URL, params={**params, "offset": offset}, timeout=90)
        if response.status_code == 404:
            break
        response.raise_for_status()
        payload = response.json()
        items = extract_records(payload)
        if not items:
            break
        for item in items:
            row = normalize(item, today)
            if row:
                records[row["source_id"]] = row
        total = int(payload.get("totalRecords") or len(records))
        offset += len(items)
        if len(items) < PAGE_SIZE or offset >= total:
            break
    return list(records.values())


def main():
    api_key = os.environ.get("SAM_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("SAM_API_KEY is not set in this repository's Actions secrets.")
    today = datetime.now(timezone.utc).date()
    sam_rows = fetch_sam(api_key, today)
    existing = json.loads(OUT.read_text()) if OUT.exists() else []
    combined = [row for row in existing if row.get("source") != "SAM.gov"] + sam_rows
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(combined, indent=2, ensure_ascii=False) + "\n")
    print(f"SAM.gov open opportunities: {len(sam_rows)}")


if __name__ == "__main__":
    main()
