# CS703 Phase 2: Data Understanding

Chen-Wei Weng
Date: 2026-10-02

This report covers CRISP-DM Phase 2 (Data Understanding), tasks 2.1–2.4. All numbers below are computed directly from the files collected by `scripts/collect_data.py` and present on disk under `data/raw/` and `data/processed/` as of the collection run recorded in `data/processed/collection_manifest.json` (generated 2026-10-02T19:36:01Z). Nothing in this report is a placeholder figure.

## Task 2.1 — Data Collection Report

### Sources collected this round

| Dataset | Source / ID | Access method | Time range | Rows collected | File(s) | File size |
|---|---|---|---|---|---|---|
| Parking Violations Issued — FY2026 (server-side aggregates) | NYC Open Data, Socrata `9mwx-gamw` | SoQL `$group` queries over full population (no local download) | Full population, all issue dates present in the resource | 15,691,604 (full population, confirmed by summing the borough and month aggregates) | `data/processed/violations_by_borough.csv`, `violations_by_month.csv`, `violations_by_dow.csv`, `violations_top_codes.csv` | 225 + 4,930 + 95 + 188 bytes |
| Parking Violations Issued — FY2026 (row sample) | NYC Open Data, Socrata `9mwx-gamw` | Paginated `$limit`/`$offset` fetch, no `$where` filter, no explicit ordering | Sample observed: 2024-04-07 to 2028-03-29 (see Task 2.4 for why this is wider than "FY2026") | 1,000,000 | `data/raw/violations_sample_fy2026.csv` | 58,676,355 bytes (~56.0 MB) |
| Parking Meters Locations and Status | NYC Open Data, Socrata `693u-uax6` | Full paginated download | Current snapshot (not date-stamped by source) | 15,598 | `data/raw/parking_meters.csv` | 4,397,588 bytes (~4.2 MB) |
| NYPD Police Precincts (boundaries) | NYC Open Data, Socrata `y76i-bdw7` | Full paginated download, converted to GeoJSON `FeatureCollection` | Static boundary layer | 78 features | `data/raw/nypd_precincts.geojson` | 4,039,895 bytes (~3.9 MB) |
| Historical hourly weather, NYC (Central Park coordinates 40.7829, -73.9654) | Open-Meteo Archive API | Single REST call, `temperature_2m` + `precipitation`, hourly | 2025-07-01T00:00 to 2026-06-30T23:00 | 8,760 | `data/raw/weather_fy2026.csv` | 234,509 bytes (~229 KB) |

### Known gap

The ASP (Alternate Side Parking) Suspension Calendar was scoped out of this collection round. NYC DOT publishes it only as a PDF / web page, not through a structured API or Socrata resource. It is recorded here as a known, deliberate gap rather than collected as a placeholder. If needed for Phase 3 feature engineering (holiday / suspension-day flags), it will require a one-off scrape or manual transcription, scoped separately.

### Process notes (issues encountered and fixed during collection)

Two real defects were found and fixed while building the collection pipeline, not during report writing:

1. **Heterogeneous CSV columns.** The CSV writer (`_write_csv` in `src/cs703/data/collect.py`) initially assumed every row dict had the same keys. Real Socrata rows for the meters dataset do not: optional fields such as `parking_facility_name` are present on some rows and entirely absent on others (confirmed below in Task 2.2 — only 1.1% of meter rows carry a non-blank `parking_facility_name`). The fix was to compute the header as the union of keys across all rows (`dict.fromkeys(key for row in rows for key in row.keys())`) and write missing fields as empty strings via `csv.DictWriter(..., restval="")`.
2. **Read timeouts under sustained load with no app token.** The Socrata client (`src/cs703/data/socrata_client.py`) is run without a registered `$$app_token` (anonymous/unauthenticated access). During the real collection run this produced intermittent `requests.exceptions.Timeout` errors on the larger paginated pulls (sample and meters). The fix adds retry with exponential backoff (up to 5 retries, 2^attempt second sleep, 90-second per-request timeout) around each page fetch. This is also a reportable **data-collection constraint**, not just a code bug: collecting from NYC Open Data without an API key is measurably less reliable than collecting with one, and anyone reproducing this work on a slow connection or during a Socrata load spike should expect to need the same retry behavior or should register a free app token.

### Reproduction

```
uv run python scripts/collect_data.py
```

This single entry point calls all four fetcher modules (`violations.py`, `meters.py`, `precincts.py`, `weather.py`) through `collect.run_collection()`, writes everything under `data/raw/` and `data/processed/`, and regenerates `data/processed/collection_manifest.json`, which is the single source of truth for the counts quoted in this report.

## Task 2.2 — Data Description Report

### 2.2.1 Parking Violations Issued — FY2026, row sample

| Column | Non-null rate (of 1,000,000 sample rows) | Notes |
|---|---|---|
| `issue_date` | 99.9983% | 17 blank |
| `violation_time` | 99.9996% | 4 blank; see Task 2.4 for parse-failure rate (distinct from blank rate) |
| `violation_county` | 97.1203% | 2.8797% blank; also see borough-code anomalies in Task 2.4 |
| `violation_precinct` | 100.0000% | populated, but see precinct=0 finding in Task 2.4 |
| `violation_code` | 100.0000% | 85 distinct codes observed in sample |
| `plate_type` | 100.0000% | top values: PAS 81.70%, COM 10.09%, OMT 3.38% |
| `street_name` | 99.9977% | 23 blank |

Row count: 1,000,000 (sample). File size: 58,676,355 bytes. Format: CSV with header, 7 columns, all values quoted/plain text (no typed columns — Socrata returns strings for every field in this projection).

### 2.2.2 Parking Violations Issued — FY2026, server-side aggregates (full population, 15,691,604 rows)

| File | Rows (distinct categories) | File size | Content |
|---|---|---|---|
| `violations_by_borough.csv` | 20 | 225 bytes | count of all 15,691,604 rows grouped by raw `violation_county` string |
| `violations_by_month.csv` | 178 | 4,930 bytes | count grouped by `date_trunc_ym(issue_date)` |
| `violations_by_dow.csv` | 8 | 95 bytes | count grouped by `date_extract_dow(issue_date)` (7 weekday buckets + 1 blank) |
| `violations_top_codes.csv` | 15 | 188 bytes | top 15 `violation_code` values by count |

These four files are exact, full-population counts (server-side `$group` aggregation over all 15,691,604 rows), not estimates from the 1M-row sample.

### 2.2.3 Parking Meters Locations and Status

22 columns (union across all rows): `objectid`, `meter_number`, `status`, `pay_by_cell_number`, `meter_hours`, `facility`, `borough`, `on_street`, `side_of_street`, `from_street`, `to_street`, `lat`, `long`, `x`, `y`, `location`, five `:@computed_region_*` geography-join columns, and `parking_facility_name`.

| Column | Non-blank rate (of 15,598 rows) |
|---|---|
| `borough` | 100.0% |
| `on_street`, `to_street`, `lat`, `long`, `x`, `y`, `location` | 100.0% |
| `status` | 99.8% |
| `meter_hours` | 99.7% |
| `facility` | 99.0% |
| `parking_facility_name` | 1.1% (174 of 15,598) |

Row count: 15,598. File size: 4,397,588 bytes. The low fill rate on `parking_facility_name` is the sparse field responsible for process-note #1 above (it is a genuinely optional field in the source, not a collection defect).

### 2.2.4 NYPD Police Precincts (boundaries)

78 GeoJSON `Feature` entries, geometry type `MultiPolygon`. Properties per feature: `precinct` (string, e.g. `"1"`), `shape_leng`, `shape_area`. No borough name or code is carried in this resource. Precinct numbers observed range from 1 to 123, all 78 distinct (no duplicates). File size: 4,039,895 bytes.

### 2.2.5 Historical hourly weather (Open-Meteo)

Columns: `time` (ISO 8601 local, America/New_York), `temperature_2m` (°C), `precipitation` (mm). 8,760 rows = 365 days × 24 hours, 2025-07-01T00:00 through 2026-06-30T23:00 inclusive. 0 missing values in either numeric column. File size: 234,509 bytes.

## Task 2.3 — Data Exploration Report

### Violations by borough (full population, 15,691,604 rows, server-side aggregate)

| Borough code | Count | Share |
|---|---|---|
| NY | 3,671,836 | 23.40% |
| QN | 2,227,592 | 14.20% |
| K | 1,898,037 | 12.10% |
| BK | 1,860,666 | 11.86% |
| Q | 1,797,770 | 11.46% |
| BX | 1,765,548 | 11.25% |
| MN | 955,473 | 6.09% |
| ST | 499,211 | 3.18% |
| (blank) | 398,664 | 2.54% |
| Kings | 260,556 | 1.66% |
| Bronx | 131,523 | 0.84% |
| R | 124,672 | 0.80% |
| Qns | 98,739 | 0.63% |
| Rich | 803 | 0.01% |
| O | 504 | 0.00% |
| QNS | 6 | 0.00% |
| q, 106, NYPAS, NT | 1 each | 0.00% |

Manhattan (under its various codes) is the single largest reporting borough, followed by Queens and Brooklyn. See Task 2.4 for discussion of the 20-way code fragmentation — this is a data-quality finding, not a geographic one.

### Violations by month, FY2026 window (full population)

| Month | Count |
|---|---|
| 2025-07 | 1,464,814 |
| 2025-08 | 1,361,420 |
| 2025-09 | 1,288,424 |
| 2025-10 | 1,402,653 |
| 2025-11 | 1,359,300 |
| 2025-12 | 1,081,647 |
| 2026-01 | 1,090,486 |
| 2026-02 | 948,206 |
| 2026-03 | 1,448,363 |
| 2026-04 | 1,395,552 |
| 2026-05 | 1,354,442 |
| 2026-06 | 1,083,558 |

These 12 FY2026 months sum to 15,278,865 rows (97.37% of the 15,691,604-row total). The remaining 2.63% falls outside the FY2026 window; see Task 2.4 — "issue_date range integrity" for the breakdown, which is a genuine data-quality issue rather than part of the seasonal pattern. Within the valid window, volume is lowest in December–February (holiday season / fewer enforcement days per month) and highest in July and March.

### Violations by day of week (full population, `date_extract_dow`: 0 = Sunday … 6 = Saturday per Socrata/Postgres convention)

| Day | Count | Share |
|---|---|---|
| 0 — Sunday | 1,411,130 | 8.99% |
| 1 — Monday | 2,297,445 | 14.64% |
| 2 — Tuesday | 2,554,987 | 16.28% |
| 3 — Wednesday | 2,376,159 | 15.14% |
| 4 — Thursday | 2,601,430 | 16.58% |
| 5 — Friday | 2,455,201 | 15.65% |
| 6 — Saturday | 1,993,396 | 12.70% |
| (blank) | 1,856 | 0.01% |

Weekday enforcement (Mon–Fri) clearly exceeds weekend enforcement; Sunday is the lowest single day.

### Violations by hour of day (1,000,000-row sample only — not a full-population statistic)

`violation_time` is a non-standard text format (e.g. `"0225P"`) that SoQL cannot aggregate server-side, so this distribution is computed locally from the sample via `hour_of_day_distribution()` in `src/cs703/data/analysis.py`. Of 1,000,000 sample rows, 999,934 produced a valid 0–23 hour; 66 rows (0.0066%) failed to parse and were excluded (see Task 2.4 for exactly why).

| Hour | Count | Hour | Count | Hour | Count | Hour | Count |
|---|---|---|---|---|---|---|---|
| 0 | 13,194 | 6 | 26,731 | 12 | 79,469 | 18 | 28,595 |
| 1 | 11,172 | 7 | 56,348 | 13 | 80,264 | 19 | 20,754 |
| 2 | 9,576 | 8 | 82,920 | 14 | 79,326 | 20 | 24,438 |
| 3 | 7,915 | 9 | 86,989 | 15 | 65,843 | 21 | 20,478 |
| 4 | 7,703 | 10 | 74,644 | 16 | 49,963 | 22 | 17,298 |
| 5 | 11,945 | 11 | 83,343 | 17 | 45,728 | 23 | 15,298 |

The busiest hour is 09:00 (86,989 violations, 8.70% of parsed sample rows), with a broad midday-to-afternoon peak (08:00–15:00) and a trough overnight (02:00–04:00).

### Top 15 violation codes (full population)

| Code | Count | Share of all 15,691,604 |
|---|---|---|
| 36 | 3,946,887 | 25.15% |
| 21 | 1,801,309 | 11.48% |
| 38 | 1,250,632 | 7.97% |
| 14 | 944,103 | 6.02% |
| 7 | 887,233 | 5.65% |
| 5 | 715,380 | 4.56% |
| 40 | 699,489 | 4.46% |
| 20 | 598,149 | 3.81% |
| 71 | 518,962 | 3.31% |
| 15 | 488,051 | 3.11% |
| 43 | 471,583 | 3.01% |
| 46 | 329,717 | 2.10% |
| 70 | 309,847 | 1.98% |
| 31 | 292,865 | 1.87% |
| 69 | 290,233 | 1.85% |

The top 15 of 85+ distinct codes already account for 86.32% of all violations. Code 36 alone is a quarter of all violations citywide. This collection round did not fetch the DOF violation-code description lookup table, so codes are reported numerically only; a code-to-description join is a Phase 3 task if needed.

### Parking meters by borough

| Borough | Meters | Share |
|---|---|---|
| Manhattan | 5,082 | 32.58% |
| Brooklyn | 4,254 | 27.27% |
| Queens | 4,242 | 27.20% |
| Bronx | 1,681 | 10.78% |
| Staten Island | 339 | 2.17% |

Meter density by borough roughly tracks violation share for Manhattan and the outer boroughs, though Brooklyn and Queens carry near-equal meter counts despite Brooklyn's higher violation share.

### Weather, monthly summary (FY2026, 8,760 hourly readings)

| Month | Avg. temperature (°C) | Total precipitation (mm) | Hours |
|---|---|---|---|
| 2025-07 | 26.5 | 107.5 | 744 |
| 2025-08 | 23.2 | 22.0 | 744 |
| 2025-09 | 20.7 | 126.3 | 720 |
| 2025-10 | 14.0 | 107.7 | 744 |
| 2025-11 | 7.2 | 52.8 | 720 |
| 2025-12 | -0.3 | 77.7 | 744 |
| 2026-01 | -2.6 | 66.1 | 744 |
| 2026-02 | -3.1 | 51.9 | 672 |
| 2026-03 | 6.7 | 113.1 | 744 |
| 2026-04 | 12.6 | 80.3 | 720 |
| 2026-05 | 17.8 | 92.2 | 744 |
| 2026-06 | 23.7 | 89.4 | 720 |

Coldest month is February 2026 (-3.1°C average); warmest is July 2025 (26.5°C average). Precipitation is heaviest in September 2025 and March 2026.

## Task 2.4 — Data Quality Report

### Null / blank rates (1,000,000-row sample, the six columns used for the duplicate check below)

| Column | Null/blank rate |
|---|---|
| `issue_date` | 0.0017% |
| `violation_time` | 0.0004% |
| `violation_county` | 2.8797% |
| `violation_precinct` | 0.0000% |
| `violation_code` | 0.0000% |
| `street_name` | 0.0023% |

### Duplicate rows

Using the composite key (`issue_date`, `violation_time`, `violation_county`, `violation_precinct`, `violation_code`, `street_name`), the sample contains 25,470 duplicate rows beyond the first occurrence (2.55% of 1,000,000). Caveat: the sample projection (`SAMPLE_COLUMNS` in `src/cs703/data/violations.py`) does not include a unique record identifier such as a summons number, so this figure is an upper-bound proxy for true duplicate tickets, not a confirmed duplicate-summons count — two distinct violations issued at the same place, minute, and code would also collide on this key.

### `violation_precinct = "0"`

468,186 of 1,000,000 sample rows (46.82%) have `violation_precinct = "0"`. This is the single largest data-quality finding in this report — nearly half the sample carries no usable precinct code. A plausible explanation is that camera-issued violations (bus lane, red light, etc.) are not attributed to a patrol precinct in this feed, but that is not confirmed from the fields collected here and needs investigation in Phase 3 before precinct-level aggregation is used as a modeling unit.

A further 9 sample rows carry implausible precinct numbers above the NYPD's actual range (max real precinct is in the 120s): `125` (×2), `806` (×2), `163` (×1), `161` (×4). Low severity, but these should be excluded or flagged before precinct-level joins.

### Borough code anomalies

`violation_county` is a free-text field, not a constrained code. Only `{NY, BX, K, Q, R}` would be the "clean" 5-borough set; the sample instead shows 10 distinct values (`NY, QN, BK, Q, BX, K, MN, ST, R`, plus blank) and the full population shows 20 distinct values, including full borough names (`Kings`, `Bronx`), mixed case (`q`), a bare number (`106`), an apparent agency code (`NYPAS`), and other noise (`O`, `NT`, `Rich`, `QNS`, `Qns`). A borough-code normalization mapping (collapsing all variants to the canonical 5 boroughs, with an explicit "unknown" bucket for blank/`O`/`NT`/`106`/`NYPAS`) will be required before any borough-level modeling in Phase 3.

### `issue_date` range integrity

The dataset is named "Parking Violations Issued – Fiscal Year 2026" but is not strictly scoped to FY2026 issue dates. The full-population month aggregate (`violations_by_month.csv`) spans 178 distinct year-months from 1971-09 to 2068-04:

| Bucket | Months | Rows | Share of 15,691,604 |
|---|---|---|---|
| Within FY2026 (2025-07 to 2026-06) | 12 | 15,278,865 | 97.37% |
| 2025-06 (one month immediately before FY start) | 1 | 403,351 | 2.57% |
| Other out-of-range months (1971-09 to 2025-05, and 2026-07 to 2068-04) | 164 | 7,532 | 0.05% |
| Null/unparseable `issue_date` (blank `date_trunc_ym` group) | — | 1,856 | 0.01% |

The 2025-06 spike is plausibly late-period/adjacent-fiscal-year entries and is not necessarily an error. The 164-month long tail scattered across nearly a century (1971–2068), each with very small counts, is almost certainly data-entry error (mis-typed years) rather than real violations issued decades in the past or future. This also explains why the 1,000,000-row sample's observed date range (2024-04-07 to 2028-03-29) is wider than FY2026: `fetch_sample()` applies no `$where` date filter, so a small number of these out-of-range rows are included in the sample along with genuine FY2026 rows. Any date-based filtering in Phase 3 should explicitly clip to the FY2026 window rather than trusting the resource name.

### `violation_time` parsing

`parse_violation_time_to_hour()` in `src/cs703/data/analysis.py` rejects a value unless it is exactly 5 characters, the first 4 are digits, the 5th is `A` or `P`, and the resulting 0–23 hour (after applying a +12 offset for `P`) falls in range. It does **not** separately validate that the raw two-digit hour portion is in the expected 12-hour-clock range of 1–12 before applying that offset. In principle this means a malformed value such as `"1300A"` (raw digit-hour 13, suffix `A`) would be accepted and parsed as hour 13 instead of being rejected as invalid, silently corrupting the hour-of-day distribution.

Checking the actual 1,000,000-row sample against this failure mode specifically:

- 0 rows have a raw digit-hour of 13–23 paired with suffix `A` (the dangerous combination) — the bug does not currently corrupt any value in this sample.
- 1,815 rows have raw digit-hour `00` with suffix `A`, and 1 row has raw digit-hour `00` with suffix `P`. Neither is a valid 12-hour-clock hour (valid range is 01–12), but both happen to resolve to the arithmetically correct 24-hour value (0 and 12 respectively) purely by coincidence of the code's arithmetic, not because the code validated them.
- 13 rows have raw digit-hour `23` with suffix `P` (e.g. `"2330P"`); these are correctly rejected by the existing final range check (23 + 12 = 35, out of 0–23) and are included in the 66 excluded/unparseable rows noted in Task 2.3.
- The remaining excluded rows are 4 blank values, 48 four-character values missing the AM/PM suffix letter (e.g. `"0948"`), and 1 value with a stray space in place of a digit (`"01 3P"`).

Conclusion: for this specific FY2026 sample, the hour-of-day table in Task 2.3 is not visibly corrupted by this bug, but the underlying validation gap is real and should be fixed (reject raw digit-hour outside 1–12, independent of the final 0–23 check) before this code is reused on a different data vintage, where the dangerous 13–23-with-`A` combination is not guaranteed to be absent.

### Meter coordinates

0 of 15,598 meter rows have `lat`/`long` outside a generous NYC bounding box (40.3–41.0°N, -74.5 to -73.5°W) or unparseable coordinates. No geocoding quality issue found in this dataset.

### Sample representativeness

`fetch_sample()` pages through the API from offset 0 with no `$where` filter and no explicit `$order`, taking whatever the first 1,000,000 rows are in the API's default ordering — it is not a random sample of the full 15,691,604-row population. Evidence: the sample's borough-code set (10 distinct values) is missing 10 of the 20 distinct codes seen in the full-population aggregate (e.g. `Kings`, `Bronx`, `Qns`, `q`, `106`, `NYPAS` do not appear at all in the sample), and the sample's observed date range (2024-04-07 to 2028-03-29) does not reach back to the full population's 1971 tail. Any Phase 3 work drawing on the row-level sample (rather than the full-population aggregates) should treat it as a convenience sample, not a representative one, and consider a server-side random sample (e.g. ordering by a hash of a row identifier) if a representative row-level sample is later needed.

### Known gap (formal record)

ASP Suspension Calendar: not collected this round. No structured API exists (PDF / web page only). Recorded here as a deliberate, documented gap per Task 2.1, carried forward as an open item for Phase 3 feature engineering (holiday / no-enforcement-day flags).

### Issue log

| # | Finding | Dataset | Severity | Status |
|---|---|---|---|---|
| 1 | `violation_precinct = "0"` in 46.82% of sample rows | Violations (sample) | High | Open — needs investigation before precinct-level modeling |
| 2 | Borough code field has 20 distinct raw values in full population, only 5 are canonical | Violations (aggregates + sample) | High | Open — needs normalization mapping |
| 3 | `issue_date` not strictly bounded to FY2026; 164-month error tail from 1971–2068 (0.05% of rows) plus 1,856 null-date rows | Violations (aggregates) | Medium | Open — needs explicit date-window filter in Phase 3 |
| 4 | 1,000,000-row sample is a convenience sample (unordered, unfiltered pagination), not representative of the full population | Violations (sample) | Medium | Open — document as limitation; consider random server-side sample if needed |
| 5 | 2.55% duplicate rows on a 6-column composite key; sample lacks a unique record ID to confirm true duplicates | Violations (sample) | Medium | Open — informational; revisit if a unique ID field is added to the sample projection |
| 6 | 9 sample rows have precinct numbers outside NYPD's real range (125, 806, 161, 163) | Violations (sample) | Low | Open — trivial to filter |
| 7 | `parse_violation_time_to_hour` does not validate raw digit-hour is 1–12 before applying AM/PM offset | `src/cs703/data/analysis.py` | Low (not currently triggered) | Open — fix recommended before reuse on other data vintages |
| 8 | `parking_facility_name` populated for only 1.1% of meter rows | Meters | Informational | Not an error — genuinely sparse optional field; required the union-of-keys CSV fix (Task 2.1) |
| 9 | Anonymous (no app-token) Socrata access produced intermittent `ReadTimeout` errors during real collection | Collection pipeline | Medium | Fixed — retry with exponential backoff (5 retries, 90s timeout); documented as a reproducibility constraint for anyone without an app token |
| 10 | ASP Suspension Calendar unavailable via structured API | (not collected) | Low | Known gap, deferred to Phase 3 scoping |
