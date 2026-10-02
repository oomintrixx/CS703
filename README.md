# CS703 — Predicting Parking Pressure Across New York City

Graduate data-mining project (CRISP-DM methodology, Fall 2026) that estimates how hard street parking is likely to be in a given NYC area and time window, using parking-violation density as a public proxy for parking pressure.

See [`docs/project-proposal.md`](docs/project-proposal.md) for the project pitch and [`docs/phase1-business-understanding.md`](docs/phase1-business-understanding.md) for the full CRISP-DM Phase 1 writeup (objectives, data sources, modeling plan, 14-week schedule).

## CRISP-DM progress

- [x] Phase 1 — Business Understanding
- [ ] Phase 2 — Data Understanding
- [ ] Phase 3 — Data Preparation
- [ ] Phase 4 — Modeling
- [ ] Phase 5 — Evaluation
- [ ] Phase 6 — Deployment / Delivery

## Setup

```bash
uv sync
cp .env.example .env   # fill in SOCRATA_APP_TOKEN / TICKETMASTER_API_KEY when needed
```

## Layout

```
docs/             CRISP-DM phase writeups
data/raw/         untouched downloads (gitignored)
data/interim/     intermediate cleaning steps (gitignored)
data/processed/   modeling-ready datasets (gitignored)
notebooks/        EDA and modeling notebooks
src/cs703/        shared project code (config, data loaders, features, models)
tests/            test suite
```
