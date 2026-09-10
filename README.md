# Waterloo Tactical Procurement Intelligence

A lightweight procurement-intelligence MVP focused on U.S. police, SWAT, special operations, and law-enforcement training opportunities.

The collector uses the public SAM.gov Get Opportunities API; the scoring layer ranks notices for tactical-training relevance.

## Run locally

```bash
pip install -r requirements.txt
set SAM_API_KEY=your_key_here
python scripts/update_sam.py
python scripts/score_opportunities.py
```

Then serve the repository root with a static server and open `app/index.html`.

## GitHub Actions

The daily workflow expects a repository secret named `SAM_API_KEY`. It runs the SAM.gov collector, scores the results, and commits the refreshed `data/opportunities.json`.

## What it is looking for

Direct signals include SWAT, tactical training, police/law-enforcement training, hostage rescue, active-shooter training, breaching, force-on-force, Simunition, and scenario-based training. Indirect signals include tactical medical, firearms training, shoot houses, training facilities, ranges, and special operations.

The score is deliberately transparent and rules-based for the MVP. The next layer can add agency-level buying history, incumbent/provider history, recurring contract detection, and procurement-contact enrichment.
