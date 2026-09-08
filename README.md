# Fremantle Procurement Intelligence MVP
Free/open-source starter. World Bank collector + local dashboard + rules-based scoring. UNGM connector is ready for an optional access token because UNGM's Notices API requires authorization.
## Run locally
`pip install -r requirements.txt`
`python scripts/update_world_bank.py`
`python scripts/score.py`
Then serve the repo root with any static server and open `app/index.html`.
## Daily
GitHub Actions runs the collectors daily when this repo is public. Add `UNGM_ACCESS_TOKEN` as a repository secret when available.
