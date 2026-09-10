import json
import re
from html.parser import HTMLParser
from pathlib import Path

import requests

OUT = Path(__file__).parents[1] / "data/opportunities.json"
URL = "https://mvendor.cgieva.com/Vendor/public/AllOpportunities.jsp"

# eVA is Virginia's statewide procurement marketplace and is used by many
# Virginia local governments as well as state agencies.
KEYWORDS = [
    "swat", "tactical training", "tactical team", "special operations",
    "hostage rescue", "breaching", "force on force", "simunition",
    "active shooter", "scenario based", "scenario-based", "shoot house",
    "firearms training", "police training", "law enforcement training",
    "tactical medical", "tactical medicine", "cq b", "close quarters",
]


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.current_href = ""
        self.current_text = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            self.current_href = dict(attrs).get("href", "")
            self.current_text = []

    def handle_data(self, data):
        if self.current_href:
            self.current_text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self.current_href:
            text = re.sub(r"\s+", " ", " ".join(self.current_text)).strip()
            self.links.append((text, self.current_href))
            self.current_href = ""
            self.current_text = []


def clean(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()


def tactical(text):
    t = clean(text).lower()
    return [k for k in KEYWORDS if k in t]


def main():
    response = requests.get(URL, timeout=60, headers={"User-Agent": "Waterloo Procurement Intelligence/1.0"})
    response.raise_for_status()

    parser = LinkParser()
    parser.feed(response.text)

    rows = json.loads(OUT.read_text()) if OUT.exists() else []
    existing = {x.get("source_id") for x in rows}
    added = 0

    for title, href in parser.links:
        if not title or "IVDetails.jsp" not in href:
            continue
        hits = tactical(title)
        if not hits:
            continue
        if href.startswith("/"):
            href = "https://mvendor.cgieva.com" + href
        if href.startswith("http://"):
            href = "https://" + href[7:]

        source_id = "eVA:" + href
        if source_id in existing:
            continue
        rows.append({
            "source": "Virginia eVA",
            "source_id": source_id,
            "title": title,
            "organization": "Virginia state/local government",
            "office": "eVA / Virginia Business Opportunities",
            "country": "United States",
            "state": "Virginia",
            "notice_type": "eVA solicitation",
            "naics": "",
            "solicitation_number": "",
            "deadline": "",
            "published": "",
            "contacts": [],
            "description": "Matched eVA tactical procurement signal: " + ", ".join(hits),
            "url": href,
            "sam_query": "",
        })
        existing.add(source_id)
        added += 1

    OUT.write_text(json.dumps(rows, indent=2, ensure_ascii=False))
    print(f"Virginia eVA tactical opportunities added: {added}")


if __name__ == "__main__":
    main()
