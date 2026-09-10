import json
import re
from pathlib import Path

P = Path(__file__).parents[1] / "data/opportunities.json"

# Direct buying signals carry the most weight. Indirect signals are useful
# because agencies often buy equipment/facilities before they buy training.
DIRECT = {
    "swat": 30,
    "special weapons and tactics": 30,
    "tactical training": 26,
    "police training": 22,
    "law enforcement training": 22,
    "hostage rescue": 22,
    "active shooter training": 22,
    "breaching": 18,
    "force on force": 18,
    "simunition": 18,
    "scenario based training": 16,
    "scenario-based training": 16,
}
INDIRECT = {
    "tactical medical": 12,
    "tactical medicine": 12,
    "firearms training": 12,
    "firearms instructor": 10,
    "shoot house": 14,
    "shooting house": 14,
    "kill house": 14,
    "training facility": 8,
    "training tower": 10,
    "range training": 8,
    "crisis response": 8,
    "critical incident": 8,
    "special operations": 12,
    "tactical": 7,
    "police": 5,
    "law enforcement": 5,
}
BUYING_SIGNAL = {
    "request for proposals": 8,
    "request for quotation": 7,
    "solicitation": 6,
    "sources sought": 5,
    "request for information": 5,
    "presolicitation": 4,
}


def clean(value):
    return re.sub(r"\s+", " ", str(value or "")).strip().lower()


def main():
    rows = json.loads(P.read_text())
    for x in rows:
        fields = [
            x.get("title"),
            x.get("description"),
            x.get("organization"),
            x.get("office"),
            x.get("notice_type"),
            x.get("naics"),
        ]
        t = clean(" ".join(map(str, fields)))

        direct_hits = [(term, pts) for term, pts in DIRECT.items() if term in t]
        indirect_hits = [(term, pts) for term, pts in INDIRECT.items() if term in t]
        buying_hits = [(term, pts) for term, pts in BUYING_SIGNAL.items() if term in t]

        score = min(100, sum(p for _, p in direct_hits) + min(25, sum(p for _, p in indirect_hits)) + min(15, sum(p for _, p in buying_hits)))

        # A federal SAM opportunity is more valuable when the title/description
        # contains a concrete training signal than when it merely says police.
        if any(term in t for term in ("training", "instruction", "course", "exercise")):
            score += 8
        if any(term in t for term in ("county police", "city police", "police department", "sheriff", "sheriff's office", "state police")):
            score += 8

        score = min(100, score)
        x["score"] = score
        x["recommendation"] = (
            "PURSUE" if score >= 65 else
            "INVESTIGATE" if score >= 45 else
            "WATCH" if score >= 25 else
            "PASS"
        )

        reasons = []
        if direct_hits:
            reasons.append("Direct: " + ", ".join(k for k, _ in direct_hits[:3]))
        if indirect_hits:
            reasons.append("Related: " + ", ".join(k for k, _ in indirect_hits[:3]))
        if buying_hits:
            reasons.append("Buying signal: " + ", ".join(k for k, _ in buying_hits[:2]))
        x["fit_reason"] = "; ".join(reasons) if reasons else "No strong SWAT/tactical procurement signal detected."

    rows.sort(key=lambda x: x.get("score", 0), reverse=True)
    P.write_text(json.dumps(rows, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
