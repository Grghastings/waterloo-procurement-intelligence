import json
import re
from pathlib import Path

P = Path(__file__).parents[1] / "data/opportunities.json"

# Direct signals indicate that the buyer is explicitly looking for SWAT,
# tactical, special-operations, or closely related training.
DIRECT = {
    "swat": 35,
    "special weapons and tactics": 35,
    "swat training": 35,
    "swat instructor": 30,
    "tactical team training": 30,
    "tactical training": 28,
    "special operations training": 26,
    "hostage rescue": 25,
    "cqb": 24,
    "close quarters combat": 24,
    "breaching training": 22,
    "breacher training": 22,
    "active shooter training": 20,
    "force on force": 20,
    "force-on-force": 20,
    "simunition": 20,
    "utm training": 20,
    "scenario based training": 18,
    "scenario-based training": 18,
}

INDIRECT = {
    "tactical firearms": 14,
    "firearms training": 14,
    "firearms instructor": 12,
    "tactical medical": 14,
    "tactical medicine": 14,
    "shoot house": 16,
    "shooting house": 16,
    "kill house": 16,
    "tactical training facility": 15,
    "swat facility": 18,
    "training facility": 8,
    "training tower": 12,
    "tactical training tower": 15,
    "range training": 8,
    "crisis response training": 10,
    "special operations": 10,
    "law enforcement instructor": 8,
    "police training": 8,
    "law enforcement training": 8,
    "tactical": 6,
    "police": 4,
    "law enforcement": 4,
}

BUYING_SIGNAL = {
    "request for proposals": 8,
    "request for quotation": 7,
    "solicitation": 6,
    "sources sought": 6,
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
            " ".join(x.get("sam_queries", [])),
        ]
        t = clean(" ".join(map(str, fields)))

        direct_hits = [(term, pts) for term, pts in DIRECT.items() if term in t]
        indirect_hits = [(term, pts) for term, pts in INDIRECT.items() if term in t]
        buying_hits = [(term, pts) for term, pts in BUYING_SIGNAL.items() if term in t]

        score = min(
            100,
            sum(p for _, p in direct_hits)
            + min(30, sum(p for _, p in indirect_hits))
            + min(15, sum(p for _, p in buying_hits)),
        )

        if any(term in t for term in ("training", "instruction", "course", "exercise")):
            score += 8

        if any(term in t for term in (
            "county police", "city police", "police department", "sheriff",
            "sheriff's office", "state police", "highway patrol", "law enforcement"
        )):
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
