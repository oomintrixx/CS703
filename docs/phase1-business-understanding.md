# CS703 Phase 1: Business Understanding

**Predicting Parking Pressure Across New York City**

Chen-Wei Weng
Date: September 18, 2026

## Task 1.1 — Determine Business Objectives

### Background

New York City drivers lose significant time, fuel, and money hunting for street parking. Because the city does not publish real-time occupancy data, no reliable tool currently tells a driver where parking is likely to be available at a given time and place. Parking violations — issued at a rate of roughly 10 million per year across the five boroughs — represent one of the richest public signals of curb-space competition. This project will mine that signal, alongside meter infrastructure, street geography, weather, and event data, to build a model that estimates parking pressure (how hard parking is likely to be) by area and time window.

### Business Objectives

**Primary Objective:** Develop a predictive model that estimates parking pressure (high / medium / low difficulty) for a given NYC location and time window, enabling drivers, fleet operators, and mobility applications to make better curb-space decisions.

**Secondary Objectives:**

- Identify the spatial and temporal patterns in parking violations across NYC precincts and blockfaces.
- Disentangle enforcement intensity from true parking demand so that the pressure signal reflects availability, not patrol concentration.
- Produce a prototype decision-support output — a ranked list of lower-pressure alternatives within a short radius — that demonstrates real-world utility.

### Business Success Criteria

| Criterion | Measure of Success |
|---|---|
| Pressure-class prediction (high/med/low) beats historical-average baseline | Accuracy or F1-score on held-out time period meaningfully exceeds baseline |
| Enforcement bias identified and addressed | Documented normalization method with before/after validation |
| Spatial coverage | Model covers all five boroughs at precinct level; blockface level for at least one borough |
| Actionable output | Prototype returns top-3 lower-pressure zones within 0.5 miles of a query point |

### Stakeholders

| Stakeholder | Role | Interest |
|---|---|---|
| Mr. N., KG695 | Academic sponsor | Rigor, reproducibility, CRISP-DM compliance |
| NYC Dept. of Transportation | Primary operational | Reduce cruising congestion and emissions |
| Delivery / service fleet operators | Secondary operational | Recover billable hours lost to curb search |
| Navigation / mobility app developers | Tertiary operational | "Parking ease" layer as user-retention feature |

### Constraints

- **Scope:** NYC public datasets only; no proprietary sensor or live-occupancy feed.
- **Timeline:** Fall 2026 semester (~14 weeks from project kick-off, September 11, 2026).
- **Resources:** Single researcher; tools limited to public or academic-licensed platforms.
- **Data limitation:** Violation density is a proxy for demand, not a direct measure of occupancy. The enforcement-vs-demand separation is a required deliverable, not an optional refinement.

## Task 1.2 — Assess the Situation

### Inventory of Resources

**Data Resources (all public, no cost)**

| Dataset | Source | Size / Cadence | Access |
|---|---|---|---|
| Parking Violations Issued (FY) | NYC Open Data | ~10M rows/year; annual + monthly update | CSV / Socrata API |
| Open Parking and Camera Violations | NYC Open Data | Real-time adjudication | Socrata API |
| Parking Meter Locations & Status | NYC Open Data | ~14K meters; periodic update | CSV / API |
| ParkNYC Blockface Rates | NYC DOT | Rates and hours by blockface | CSV |
| NYPD Precinct Boundaries | NYC Open Data | Static shapefile | GeoJSON |
| NYC Street Centerline (LION) | NYC DCP | Static; updated quarterly | Shapefile |
| ASP Suspension Calendar | NYC DOT | Annual calendar | PDF / web scrape |
| Open-Meteo Historical Weather | Open-Meteo.com | Hourly; global coverage | REST API (free) |
| NYC Permitted Event Information | NYC Open Data | Event-level; ongoing | CSV / API |
| Ticketmaster Discovery API | Ticketmaster | Venue events; rate-limited | REST API (free tier) |

**Personnel:** One graduate researcher (project lead and sole analyst).

**Software / Infrastructure:** Python (pandas, scikit-learn, XGBoost, geopandas, matplotlib/seaborn); Jupyter Notebooks; GitHub for version control; Google Colab or local CPU for training.

### Requirements, Assumptions, and Constraints

**Requirements:**

- All data must be public and free to use for academic purposes.
- The model must be explainable: feature importance and decision rationale must be documentable.
- Time-based train/test split is required; the model must never use the future to predict the past.
- Enforcement normalization must be documented and validated before final model evaluation.

**Assumptions:**

- Parking violation density is a valid proxy for parking pressure when controlled for enforcement patterns.
- Historical violation rates are stable enough year-over-year that a multi-year training corpus is appropriate.
- Weather and event data provide incremental predictive lift over time-of-day and day-of-week features alone.
- Scope may be narrowed to one borough or to metered blocks only if data volume or timeline demands it.

**Constraints:**

- No access to proprietary occupancy sensors, camera feeds, or GPS trace data.
- Ticketmaster API rate limits may require caching or sampling for event data.
- Geocoding street-and-house-number addresses to blockface level introduces noise that must be quantified.

### Risks and Contingencies

| Risk | Likelihood | Impact | Contingency |
|---|---|---|---|
| Enforcement-vs-demand separation proves intractable | Medium | High | Fall back to a clearly labeled "violation density predictor" and document the limitation |
| Geocoding quality degrades the blockface model | Medium | Medium | Stay at precinct level; blockface = stretch goal |
| Ticketmaster API access suspended or rate-limited | Low | Low | Drop event features; use NYC Permitted Events only |
| Training time exceeds local CPU budget | Low | Medium | Reduce spatial resolution or training window; use Colab GPU |
| Semester timeline slips | Medium | Medium | Scope to Manhattan only and one calendar year of violations |

### Terminology

| Term | Definition |
|---|---|
| Parking pressure | Estimated difficulty of finding a legal curb space in a given area and time window |
| Enforcement intensity | The rate of officer patrols and citation activity in an area, independent of actual occupancy |
| Blockface | One side of a city block between two consecutive intersections; the smallest spatial unit for parking regulation |
| Precinct | One of 77 NYPD patrol precincts; the coarse spatial aggregation unit for this project |
| Time-based split | A train/test partition that uses earlier dates for training and later dates for evaluation, preventing data leakage |

## Task 1.3 — Determine Data-Mining Goals

### Data-Mining Problem Statement

Given a spatial unit (NYC police precinct or blockface) and a time window (hour of day + day of week + date), predict which of three parking-pressure classes — High, Medium, or Low — best describes how difficult street parking is likely to be. The prediction should improve over a simple historical-average baseline and should be accompanied by a ranked list of nearby lower-pressure zones.

### Data-Mining Goals

- **Classification:** Build a supervised multi-class classifier that predicts parking pressure class (High / Medium / Low) for a given area-time combination.
- **Enforcement Normalization:** Develop and validate a method to separate enforcement-driven violation spikes from demand-driven ones, producing a cleaned "demand signal" as a derived feature.
- **Feature Importance:** Identify which features (time of day, day of week, weather, proximity to events, meter rate, land use, street-cleaning schedule) contribute most to pressure prediction.
- **Proximity Ranking:** For any query point, return the top-3 nearby zones predicted to have lower pressure at the same time window.

### Output of Data Mining

| Output | Type | Description |
|---|---|---|
| Pressure class | Predicted label | High / Medium / Low per area-time record |
| Probability scores | Model output | Confidence per class (enables soft thresholding) |
| Feature importance ranking | Explainability artifact | Ranked list of predictors with coefficients or SHAP values |
| Enforcement normalization factors | Derived dataset | Per-precinct adjustment multipliers with validation metrics |
| Proximity recommendation list | Application output | Top-3 lower-pressure zones within 0.5 miles of query point |

### Modeling Approach

**Step 1 — Baseline:** Historical average violation count per precinct per hour-of-week. Establishes the floor that more sophisticated models must beat.

**Step 2 — Feature Engineering:**

- Temporal: hour, day of week, month, holiday flag, street-cleaning day flag
- Spatial: precinct ID, borough, land-use category, distance to nearest meter cluster
- External: temperature, precipitation, nearby event flag (within 0.5 mi)
- Enforcement control: rolling 4-week citation rate per officer-hour or a precinct-level enforcement index

**Step 3 — Model Candidates:**

| Model | Rationale |
|---|---|
| Logistic Regression | Interpretable baseline; fast to train; easy coefficient inspection |
| Random Forest | Handles non-linear interactions; built-in feature importance |
| Gradient Boosted Trees (XGBoost) | Strong on tabular data with temporal seasonality; primary candidate |

**Step 4 — Evaluation:** Time-based 80/20 train/test split (train on earlier years, test on most recent year). Metrics: weighted F1-score, per-class precision/recall, and comparison to the historical-average baseline.

### Data-Mining Success Criteria

| Criterion | Target |
|---|---|
| Weighted F1-score on test set | > baseline F1 by ≥ 5 percentage points |
| Per-class recall for "High" pressure | ≥ 0.70 (minimize missed high-demand warnings) |
| Enforcement normalization validation | Adjusted signal correlates better with meter transaction volume than raw violation count |
| Proximity recommendation latency | Top-3 lookup executes in < 2 seconds on a single CPU |

## Task 1.4 — Produce a Project Plan

Project start: September 11, 2026. All dates are Friday end-of-week submission targets unless noted. One researcher throughout.

### Phase 1 — Business Understanding (Weeks 1–2)

| Task | Subtask | Owner | Start | Due | Deliverable |
|---|---|---|---|---|---|
| 1.1 Determine Business Objectives | Draft background, objectives, success criteria, stakeholder table, constraints | Researcher | Sep 11 | Sep 18 | Project Scope Doc — Part 1 |
| 1.2 Assess the Situation | Inventory resources; document assumptions, risks, terminology | Researcher | Sep 15 | Sep 18 | Project Scope Doc — Part 2 |
| 1.3 Determine Data-Mining Goals | Define problem statement, modeling goals, output types, success criteria | Researcher | Sep 15 | Sep 18 | Data-Mining Scope Document |
| 1.4 Produce a Project Plan | Build detailed task-level plan with milestones and dates | Researcher | Sep 17 | Sep 18 | Project/Resource Plan |

### Phase 2 — Data Understanding (Weeks 3–4)

| Task | Subtask | Owner | Start | Due | Deliverable |
|---|---|---|---|---|---|
| 2.1 Collect Initial Data | Register for all APIs; download violation CSVs (3 years); download meter, boundary, weather datasets | Researcher | Sep 19 | Sep 25 | Initial data report |
| 2.2 Describe the Data | Document schema, row counts, date ranges, null rates, and file sizes for each source | Researcher | Sep 22 | Sep 25 | Data description report |
| 2.3 Explore the Data | Visualize violation volume by precinct, hour, day of week; map hotspots; plot seasonal trends | Researcher | Sep 26 | Oct 2 | EDA notebook |
| 2.4 Verify Data Quality | Identify missing geocodes, duplicate records, date-range gaps, and outlier precincts | Researcher | Sep 26 | Oct 2 | Data quality report with issue log |

### Phase 3 — Data Preparation (Weeks 5–7)

| Task | Subtask | Owner | Start | Due | Deliverable |
|---|---|---|---|---|---|
| 3.1 Select Data | Decide final features and spatial resolution; document exclusions | Researcher | Oct 3 | Oct 9 | Feature selection memo |
| 3.2 Clean Data | Remove nulls, deduplicate, standardize address formats, fix timezone offsets | Researcher | Oct 3 | Oct 9 | Cleaned violation + meter dataset |
| 3.3 Construct Features | Build hour/day/month flags; holiday and ASP calendar join; weather merge; event proximity flag | Researcher | Oct 10 | Oct 16 | Feature-engineered dataset |
| 3.4 Enforcement Normalization | Compute per-precinct enforcement index; adjust violation counts; validate against meter transactions | Researcher | Oct 10 | Oct 16 | Normalized demand signal + validation memo |
| 3.5 Aggregate to Area-Time Records | Aggregate to precinct × hour-of-week; label pressure class using percentile thresholds | Researcher | Oct 17 | Oct 23 | Labeled modeling dataset |

### Phase 4 — Modeling (Weeks 8–10)

| Task | Subtask | Owner | Start | Due | Deliverable |
|---|---|---|---|---|---|
| 4.1 Select Modeling Techniques | Finalize model candidates (LR, RF, XGBoost); justify selection | Researcher | Oct 24 | Oct 30 | Modeling approach memo |
| 4.2 Design Test Harness | Implement time-based 80/20 split; set up cross-validation; define evaluation metrics | Researcher | Oct 24 | Oct 30 | Evaluation framework notebook |
| 4.3 Build Baseline Model | Historical average by precinct and hour-of-week; compute baseline F1 | Researcher | Oct 31 | Nov 6 | Baseline model results |
| 4.4 Build and Tune Candidate Models | Train LR, RF, and XGBoost; tune hyperparameters via cross-validation | Researcher | Oct 31 | Nov 13 | Trained model files + tuning log |
| 4.5 Assess Models | Compare F1, precision, recall per class; generate SHAP feature importance; select best model | Researcher | Nov 14 | Nov 20 | Model comparison report |

### Phase 5 — Evaluation (Weeks 11–12)

| Task | Subtask | Owner | Start | Due | Deliverable |
|---|---|---|---|---|---|
| 5.1 Evaluate Results vs. Business Goals | Verify model meets F1 target and High-recall threshold; confirm enforcement normalization validates | Researcher | Nov 21 | Nov 27 | Evaluation vs. business goals memo |
| 5.2 Review Process | Identify steps revisited, data issues encountered, and deviations from plan | Researcher | Nov 21 | Nov 27 | Process review notes |
| 5.3 Determine Next Steps | Scope the proximity-ranking prototype; identify any required model refinements | Researcher | Nov 28 | Dec 4 | Next-steps memo |

### Phase 6 — Deployment / Delivery (Weeks 13–14)

| Task | Subtask | Owner | Start | Due | Deliverable |
|---|---|---|---|---|---|
| 6.1 Build Proximity Prototype | Implement top-3 lower-pressure zone lookup for any query point and time window | Researcher | Dec 5 | Dec 11 | Working prototype (notebook) |
| 6.2 Produce Final Report | Compile all phase documents, EDA, model results, and prototype into a final project report | Researcher | Dec 5 | Dec 11 | Final project report |
| 6.3 Prepare Final Presentation | Build slide deck summarizing problem, approach, results, and demo | Researcher | Dec 8 | Dec 14 | Presentation slide deck |
| 6.4 Final Submission | Submit all deliverables to Mr. N. | Researcher | — | Dec 18 | All deliverables submitted |

### Milestone Summary

| Milestone | Target Date |
|---|---|
| Phase 1 complete — Business Understanding documents submitted | Sep 18, 2026 |
| Phase 2 complete — Data collected, described, explored, and quality-checked | Oct 2, 2026 |
| Phase 3 complete — Labeled modeling dataset ready | Oct 23, 2026 |
| Phase 4 complete — Best model selected | Nov 20, 2026 |
| Phase 5 complete — Evaluation and next steps documented | Dec 4, 2026 |
| Phase 6 complete — Final report and presentation submitted | Dec 18, 2026 |
