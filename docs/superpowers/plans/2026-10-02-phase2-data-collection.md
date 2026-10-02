# Phase 2 Data Collection & Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the data-collection code for the five core Phase 2 sources (NYC parking violations, meters, precincts, weather) and use the real collected data to write `docs/phase2-data-understanding.md`, covering CRISP-DM tasks 2.1–2.4.

**Architecture:** A thin shared Socrata pagination client (`socrata_client.py`) underlies per-source fetcher modules (`violations.py`, `meters.py`, `precincts.py`, `weather.py`). A pure, network-free `analysis.py` computes the statistics the report needs (hour parsing, null rates, duplicates, borough-code counts) so it's unit-testable without mocking HTTP. `collect.py` orchestrates all fetchers into `run_collection()`, writing files to `data/raw/` and `data/processed/` plus a `collection_manifest.json` that is the single source of truth for every number later quoted in the report. `scripts/collect_data.py` is a thin CLI wrapper. The report itself is written by hand from the real manifest + analysis output — there is no templating engine (YAGNI for a one-off document).

**Tech Stack:** Python 3.12, `requests`, `pandas`, `pytest` (new dev dependency), stdlib `unittest.mock` for HTTP mocking — no new runtime dependencies beyond what's already in `pyproject.toml`.

## Global Constraints

- Reference design: `docs/superpowers/specs/2026-10-02-phase2-data-collection-design.md` — this plan implements it exactly; do not expand scope (no ASP calendar, no 5 secondary sources, no charts/notebooks).
- Violations dataset: Socrata resource id `9mwx-gamw` ("Parking Violations Issued - Fiscal Year 2026"), confirmed 15,691,604 rows.
- Meters dataset: resource id `693u-uax6`, confirmed 15,598 rows.
- Precincts dataset: resource id `y76i-bdw7`, confirmed 78 rows.
- Weather: Open-Meteo archive API, `https://archive-api.open-meteo.com/v1/archive`, NYC Central Park coordinates `latitude=40.7829&longitude=-73.9654`, date range `2025-07-01` to `2026-06-30`.
- No Socrata app token available — client must work with `app_token=None` and must not break when it's set later via `.env` (`SOCRATA_APP_TOKEN`, already wired in `src/cs703/config.py`).
- Sample size for raw violations rows: exactly 1,000,000 rows (not the full 15.69M).
- Report file: single Markdown file at `docs/phase2-data-understanding.md`, four sections matching tasks 2.1–2.4, tables only (no embedded images).
- Follow existing project layout from `docs/superpowers/specs/2026-10-02-project-scaffold-design.md`: package code under `src/cs703/`, scripts under `scripts/`, tests under `tests/`.

---

### Task 1: Add pytest and scaffold the data test package

**Files:**
- Modify: `pyproject.toml` (add `pytest` as dev dependency via `uv add --dev pytest`)
- Create: `tests/data/__init__.py`

**Interfaces:**
- Produces: a working `uv run pytest` command that collects tests under `tests/`.

- [ ] **Step 1: Add pytest as a dev dependency**

Run: `uv add --dev pytest`

- [ ] **Step 2: Create the test subpackage**

Create `tests/data/__init__.py` (empty file).

- [ ] **Step 3: Verify pytest runs with zero tests collected**

Run: `uv run pytest tests/ -v`
Expected: `collected 0 items` (no errors, no failures — confirms pytest + package discovery work before any real tests exist)

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock tests/data/__init__.py
git commit -m "test: add pytest dev dependency and tests/data package"
```

---

### Task 2: Socrata pagination client

**Files:**
- Create: `src/cs703/data/socrata_client.py`
- Test: `tests/data/test_socrata_client.py`

**Interfaces:**
- Produces: `fetch_all(resource_id: str, select: str | None = None, where: str | None = None, group: str | None = None, order: str | None = None, page_size: int = 50_000, max_rows: int | None = None, app_token: str | None = None, base_url: str = "https://data.cityofnewyork.us/resource") -> list[dict]` — used by every fetcher module in Tasks 3–6.

- [ ] **Step 1: Write the failing tests**

```python
# tests/data/test_socrata_client.py
from unittest.mock import patch, Mock

from cs703.data.socrata_client import fetch_all


def _mock_response(rows):
    resp = Mock()
    resp.json.return_value = rows
    resp.raise_for_status.return_value = None
    return resp


@patch("cs703.data.socrata_client.requests.get")
def test_fetch_all_paginates_until_short_page(mock_get):
    page1 = [{"id": i} for i in range(3)]
    page2 = [{"id": i} for i in range(3, 5)]  # shorter than page_size -> last page
    mock_get.side_effect = [_mock_response(page1), _mock_response(page2)]

    rows = fetch_all("abcd-1234", page_size=3)

    assert rows == page1 + page2
    assert mock_get.call_count == 2


@patch("cs703.data.socrata_client.requests.get")
def test_fetch_all_stops_at_max_rows(mock_get):
    page1 = [{"id": i} for i in range(3)]
    page2 = [{"id": i} for i in range(3, 6)]
    mock_get.side_effect = [_mock_response(page1), _mock_response(page2)]

    rows = fetch_all("abcd-1234", page_size=3, max_rows=5)

    assert rows == (page1 + page2)[:5]


@patch("cs703.data.socrata_client.requests.get")
def test_fetch_all_builds_expected_query_params(mock_get):
    mock_get.side_effect = [_mock_response([])]

    fetch_all(
        "abcd-1234",
        select="a,b",
        where="c > 1",
        group="a",
        order="a",
        page_size=10,
        app_token="tok123",
    )

    called_url = mock_get.call_args.args[0]
    called_params = mock_get.call_args.kwargs["params"]
    assert called_url == "https://data.cityofnewyork.us/resource/abcd-1234.json"
    assert called_params["$select"] == "a,b"
    assert called_params["$where"] == "c > 1"
    assert called_params["$group"] == "a"
    assert called_params["$order"] == "a"
    assert called_params["$limit"] == 10
    assert called_params["$offset"] == 0
    assert called_params["$$app_token"] == "tok123"


@patch("cs703.data.socrata_client.requests.get")
def test_fetch_all_omits_app_token_param_when_none(mock_get):
    mock_get.side_effect = [_mock_response([])]

    fetch_all("abcd-1234")

    called_params = mock_get.call_args.kwargs["params"]
    assert "$$app_token" not in called_params
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/data/test_socrata_client.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'cs703.data.socrata_client'`

- [ ] **Step 3: Write the implementation**

```python
# src/cs703/data/socrata_client.py
"""Thin pagination client for NYC Open Data (Socrata) resources."""

import requests


def fetch_all(
    resource_id: str,
    select: str | None = None,
    where: str | None = None,
    group: str | None = None,
    order: str | None = None,
    page_size: int = 50_000,
    max_rows: int | None = None,
    app_token: str | None = None,
    base_url: str = "https://data.cityofnewyork.us/resource",
) -> list[dict]:
    url = f"{base_url}/{resource_id}.json"
    rows: list[dict] = []
    offset = 0

    while True:
        params = {"$limit": page_size, "$offset": offset}
        if select:
            params["$select"] = select
        if where:
            params["$where"] = where
        if group:
            params["$group"] = group
        if order:
            params["$order"] = order
        if app_token:
            params["$$app_token"] = app_token

        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        page = response.json()
        rows.extend(page)

        if max_rows is not None and len(rows) >= max_rows:
            return rows[:max_rows]
        if len(page) < page_size:
            return rows

        offset += page_size
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/data/test_socrata_client.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/cs703/data/socrata_client.py tests/data/test_socrata_client.py
git commit -m "feat: add Socrata pagination client"
```

---

### Task 3: Violations fetcher (aggregates + sample)

**Files:**
- Create: `src/cs703/data/violations.py`
- Test: `tests/data/test_violations.py`

**Interfaces:**
- Consumes: `cs703.data.socrata_client.fetch_all(...)` (Task 2).
- Produces: `RESOURCE_ID: str`; `fetch_borough_counts(app_token=None) -> list[dict]`; `fetch_monthly_counts(app_token=None) -> list[dict]`; `fetch_day_of_week_counts(app_token=None) -> list[dict]`; `fetch_top_violation_codes(limit=15, app_token=None) -> list[dict]`; `fetch_sample(n=1_000_000, app_token=None) -> list[dict]` — all consumed by `collect.py` (Task 6).

- [ ] **Step 1: Write the failing tests**

```python
# tests/data/test_violations.py
from unittest.mock import patch

from cs703.data import violations


@patch("cs703.data.violations.fetch_all")
def test_fetch_borough_counts_groups_by_county(mock_fetch_all):
    mock_fetch_all.return_value = [{"violation_county": "NY", "count": "100"}]

    result = violations.fetch_borough_counts()

    assert result == [{"violation_county": "NY", "count": "100"}]
    _, kwargs = mock_fetch_all.call_args
    assert mock_fetch_all.call_args.args[0] == violations.RESOURCE_ID
    assert kwargs["group"] == "violation_county"
    assert kwargs["select"] == "violation_county, count(*)"


@patch("cs703.data.violations.fetch_all")
def test_fetch_monthly_counts_groups_by_month(mock_fetch_all):
    mock_fetch_all.return_value = []

    violations.fetch_monthly_counts()

    kwargs = mock_fetch_all.call_args.kwargs
    assert kwargs["group"] == "month"
    assert kwargs["select"] == "date_trunc_ym(issue_date) as month, count(*)"
    assert kwargs["order"] == "month"


@patch("cs703.data.violations.fetch_all")
def test_fetch_day_of_week_counts_groups_by_dow(mock_fetch_all):
    mock_fetch_all.return_value = []

    violations.fetch_day_of_week_counts()

    kwargs = mock_fetch_all.call_args.kwargs
    assert kwargs["group"] == "dow"
    assert kwargs["select"] == "date_extract_dow(issue_date) as dow, count(*)"


@patch("cs703.data.violations.fetch_all")
def test_fetch_top_violation_codes_orders_desc_with_limit(mock_fetch_all):
    mock_fetch_all.return_value = []

    violations.fetch_top_violation_codes(limit=15)

    args, kwargs = mock_fetch_all.call_args
    assert kwargs["group"] == "violation_code"
    assert kwargs["order"] == "count(*) DESC"
    assert kwargs["max_rows"] == 15


@patch("cs703.data.violations.fetch_all")
def test_fetch_sample_requests_selected_columns_and_row_cap(mock_fetch_all):
    mock_fetch_all.return_value = []

    violations.fetch_sample(n=1_000_000)

    kwargs = mock_fetch_all.call_args.kwargs
    assert kwargs["max_rows"] == 1_000_000
    assert "issue_date" in kwargs["select"]
    assert "violation_time" in kwargs["select"]
    assert "violation_county" in kwargs["select"]
    assert "violation_precinct" in kwargs["select"]
    assert "violation_code" in kwargs["select"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/data/test_violations.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'cs703.data.violations'`

- [ ] **Step 3: Write the implementation**

```python
# src/cs703/data/violations.py
"""Fetchers for the FY2026 Parking Violations Issued dataset."""

from cs703.data.socrata_client import fetch_all

RESOURCE_ID = "9mwx-gamw"

SAMPLE_COLUMNS = (
    "issue_date, violation_time, violation_county, violation_precinct, "
    "violation_code, plate_type, street_name"
)


def fetch_borough_counts(app_token=None) -> list[dict]:
    return fetch_all(
        RESOURCE_ID,
        select="violation_county, count(*)",
        group="violation_county",
        order="count(*) DESC",
        app_token=app_token,
    )


def fetch_monthly_counts(app_token=None) -> list[dict]:
    return fetch_all(
        RESOURCE_ID,
        select="date_trunc_ym(issue_date) as month, count(*)",
        group="month",
        order="month",
        app_token=app_token,
    )


def fetch_day_of_week_counts(app_token=None) -> list[dict]:
    return fetch_all(
        RESOURCE_ID,
        select="date_extract_dow(issue_date) as dow, count(*)",
        group="dow",
        order="dow",
        app_token=app_token,
    )


def fetch_top_violation_codes(limit: int = 15, app_token=None) -> list[dict]:
    return fetch_all(
        RESOURCE_ID,
        select="violation_code, count(*)",
        group="violation_code",
        order="count(*) DESC",
        max_rows=limit,
        app_token=app_token,
    )


def fetch_sample(n: int = 1_000_000, app_token=None) -> list[dict]:
    return fetch_all(
        RESOURCE_ID,
        select=SAMPLE_COLUMNS,
        max_rows=n,
        app_token=app_token,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/data/test_violations.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/cs703/data/violations.py tests/data/test_violations.py
git commit -m "feat: add violations aggregate and sample fetchers"
```

---

### Task 4: Meters and precincts fetchers

**Files:**
- Create: `src/cs703/data/meters.py`
- Create: `src/cs703/data/precincts.py`
- Test: `tests/data/test_meters.py`
- Test: `tests/data/test_precincts.py`

**Interfaces:**
- Consumes: `cs703.data.socrata_client.fetch_all(...)` (Task 2).
- Produces: `meters.RESOURCE_ID: str`, `meters.fetch_meters(app_token=None) -> list[dict]`; `precincts.RESOURCE_ID: str`, `precincts.fetch_precincts(app_token=None) -> list[dict]` — both consumed by `collect.py` (Task 6).

- [ ] **Step 1: Write the failing tests**

```python
# tests/data/test_meters.py
from unittest.mock import patch

from cs703.data import meters


@patch("cs703.data.meters.fetch_all")
def test_fetch_meters_requests_full_resource(mock_fetch_all):
    mock_fetch_all.return_value = [{"meter_number": "1"}]

    result = meters.fetch_meters()

    assert result == [{"meter_number": "1"}]
    assert mock_fetch_all.call_args.args[0] == meters.RESOURCE_ID
    assert "max_rows" not in mock_fetch_all.call_args.kwargs
```

```python
# tests/data/test_precincts.py
from unittest.mock import patch

from cs703.data import precincts


@patch("cs703.data.precincts.fetch_all")
def test_fetch_precincts_requests_full_resource(mock_fetch_all):
    mock_fetch_all.return_value = [{"precinct": "1"}]

    result = precincts.fetch_precincts()

    assert result == [{"precinct": "1"}]
    assert mock_fetch_all.call_args.args[0] == precincts.RESOURCE_ID
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/data/test_meters.py tests/data/test_precincts.py -v`
Expected: FAIL with `ModuleNotFoundError` for both modules

- [ ] **Step 3: Write the implementations**

```python
# src/cs703/data/meters.py
"""Fetcher for the Parking Meters Locations and Status dataset."""

from cs703.data.socrata_client import fetch_all

RESOURCE_ID = "693u-uax6"


def fetch_meters(app_token=None) -> list[dict]:
    return fetch_all(RESOURCE_ID, app_token=app_token)
```

```python
# src/cs703/data/precincts.py
"""Fetcher for the NYPD Police Precincts boundary dataset."""

from cs703.data.socrata_client import fetch_all

RESOURCE_ID = "y76i-bdw7"


def fetch_precincts(app_token=None) -> list[dict]:
    return fetch_all(RESOURCE_ID, app_token=app_token)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/data/test_meters.py tests/data/test_precincts.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/cs703/data/meters.py src/cs703/data/precincts.py tests/data/test_meters.py tests/data/test_precincts.py
git commit -m "feat: add meters and precincts fetchers"
```

---

### Task 5: Weather fetcher

**Files:**
- Create: `src/cs703/data/weather.py`
- Test: `tests/data/test_weather.py`

**Interfaces:**
- Produces: `NYC_LAT: float`, `NYC_LON: float`, `fetch_weather(start_date: str, end_date: str) -> dict` — returns the parsed Open-Meteo JSON body (dict with an `"hourly"` key containing `"time"`, `"temperature_2m"`, `"precipitation"` lists). Consumed by `collect.py` (Task 6).

- [ ] **Step 1: Write the failing test**

```python
# tests/data/test_weather.py
from unittest.mock import patch, Mock

from cs703.data import weather


@patch("cs703.data.weather.requests.get")
def test_fetch_weather_calls_archive_api_with_expected_params(mock_get):
    resp = Mock()
    resp.json.return_value = {"hourly": {"time": ["2025-07-01T00:00"], "temperature_2m": [20.0], "precipitation": [0.0]}}
    resp.raise_for_status.return_value = None
    mock_get.return_value = resp

    result = weather.fetch_weather("2025-07-01", "2026-06-30")

    assert result == resp.json.return_value
    called_url = mock_get.call_args.args[0]
    called_params = mock_get.call_args.kwargs["params"]
    assert called_url == "https://archive-api.open-meteo.com/v1/archive"
    assert called_params["latitude"] == weather.NYC_LAT
    assert called_params["longitude"] == weather.NYC_LON
    assert called_params["start_date"] == "2025-07-01"
    assert called_params["end_date"] == "2026-06-30"
    assert called_params["hourly"] == "temperature_2m,precipitation"
    assert called_params["timezone"] == "America/New_York"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/data/test_weather.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'cs703.data.weather'`

- [ ] **Step 3: Write the implementation**

```python
# src/cs703/data/weather.py
"""Fetcher for NYC historical hourly weather via the Open-Meteo archive API."""

import requests

NYC_LAT = 40.7829
NYC_LON = -73.9654
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


def fetch_weather(start_date: str, end_date: str) -> dict:
    params = {
        "latitude": NYC_LAT,
        "longitude": NYC_LON,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "temperature_2m,precipitation",
        "timezone": "America/New_York",
    }
    response = requests.get(ARCHIVE_URL, params=params, timeout=60)
    response.raise_for_status()
    return response.json()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/data/test_weather.py -v`
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add src/cs703/data/weather.py tests/data/test_weather.py
git commit -m "feat: add Open-Meteo weather fetcher"
```

---

### Task 6: Pure analysis helpers

**Files:**
- Create: `src/cs703/data/analysis.py`
- Test: `tests/data/test_analysis.py`

**Interfaces:**
- Produces: `parse_violation_time_to_hour(value: str) -> int | None`; `hour_of_day_distribution(times: list[str]) -> dict[int, int]`; `null_rates(rows: list[dict], columns: list[str]) -> dict[str, float]`; `duplicate_count(rows: list[dict], key_columns: list[str]) -> int`; `value_counts(rows: list[dict], column: str) -> dict[str, int]` — all used manually in Task 9 to compute report numbers.

- [ ] **Step 1: Write the failing tests**

```python
# tests/data/test_analysis.py
from cs703.data.analysis import (
    parse_violation_time_to_hour,
    hour_of_day_distribution,
    null_rates,
    duplicate_count,
    value_counts,
)


def test_parse_violation_time_to_hour_handles_am_pm():
    assert parse_violation_time_to_hour("0225P") == 14
    assert parse_violation_time_to_hour("1130A") == 11
    assert parse_violation_time_to_hour("1200A") == 0
    assert parse_violation_time_to_hour("1200P") == 12


def test_parse_violation_time_to_hour_handles_invalid_input():
    assert parse_violation_time_to_hour("") is None
    assert parse_violation_time_to_hour(None) is None
    assert parse_violation_time_to_hour("garbage") is None


def test_hour_of_day_distribution_counts_buckets():
    times = ["0225P", "0225P", "1130A", ""]
    result = hour_of_day_distribution(times)
    assert result == {14: 2, 11: 1}


def test_null_rates_computes_fraction_missing_or_empty():
    rows = [{"a": "1", "b": ""}, {"a": None, "b": "2"}, {"a": "3", "b": "4"}]
    result = null_rates(rows, ["a", "b"])
    assert result == {"a": 1 / 3, "b": 1 / 3}


def test_duplicate_count_counts_rows_sharing_key():
    rows = [
        {"id": "1", "v": "x"},
        {"id": "1", "v": "x"},
        {"id": "2", "v": "y"},
    ]
    assert duplicate_count(rows, ["id", "v"]) == 1


def test_value_counts_tallies_column():
    rows = [{"county": "NY"}, {"county": "NY"}, {"county": "BX"}]
    assert value_counts(rows, "county") == {"NY": 2, "BX": 1}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/data/test_analysis.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'cs703.data.analysis'`

- [ ] **Step 3: Write the implementation**

```python
# src/cs703/data/analysis.py
"""Pure, network-free helpers for the Phase 2 description/exploration/quality report."""

from collections import Counter


def parse_violation_time_to_hour(value: str | None) -> int | None:
    if not value or len(value) != 5:
        return None
    digits, suffix = value[:4], value[4]
    if not digits.isdigit() or suffix not in ("A", "P"):
        return None
    hour = int(digits[:2])
    if hour == 12:
        hour = 0
    if suffix == "P":
        hour += 12
    if not (0 <= hour <= 23):
        return None
    return hour


def hour_of_day_distribution(times: list[str]) -> dict[int, int]:
    counts: Counter[int] = Counter()
    for value in times:
        hour = parse_violation_time_to_hour(value)
        if hour is not None:
            counts[hour] += 1
    return dict(counts)


def null_rates(rows: list[dict], columns: list[str]) -> dict[str, float]:
    total = len(rows)
    result = {}
    for column in columns:
        missing = sum(1 for row in rows if not row.get(column))
        result[column] = missing / total if total else 0.0
    return result


def duplicate_count(rows: list[dict], key_columns: list[str]) -> int:
    seen: Counter[tuple] = Counter()
    for row in rows:
        key = tuple(row.get(column) for column in key_columns)
        seen[key] += 1
    return sum(count - 1 for count in seen.values() if count > 1)


def value_counts(rows: list[dict], column: str) -> dict[str, int]:
    return dict(Counter(row.get(column) for row in rows))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/data/test_analysis.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add src/cs703/data/analysis.py tests/data/test_analysis.py
git commit -m "feat: add pure analysis helpers for the Phase 2 report"
```

---

### Task 7: Collection orchestration (`collect.py` + `scripts/collect_data.py`)

**Files:**
- Create: `src/cs703/data/collect.py`
- Create: `scripts/collect_data.py`
- Test: `tests/data/test_collect.py`

**Interfaces:**
- Consumes: `violations.fetch_borough_counts/fetch_monthly_counts/fetch_day_of_week_counts/fetch_top_violation_codes/fetch_sample` (Task 3), `meters.fetch_meters` (Task 4), `precincts.fetch_precincts` (Task 4), `weather.fetch_weather` (Task 5), `cs703.config.DATA_RAW_DIR/DATA_PROCESSED_DIR/SOCRATA_APP_TOKEN` (already in repo).
- Produces: `run_collection(raw_dir: Path, processed_dir: Path, app_token: str | None = None) -> dict` — returns the manifest dict and also writes it to `processed_dir / "collection_manifest.json"`. This is the function Task 9 reads to get real numbers.

- [ ] **Step 1: Write the failing test**

```python
# tests/data/test_collect.py
import json
from unittest.mock import patch

from cs703.data.collect import run_collection


@patch("cs703.data.collect.weather.fetch_weather")
@patch("cs703.data.collect.precincts.fetch_precincts")
@patch("cs703.data.collect.meters.fetch_meters")
@patch("cs703.data.collect.violations.fetch_sample")
@patch("cs703.data.collect.violations.fetch_top_violation_codes")
@patch("cs703.data.collect.violations.fetch_day_of_week_counts")
@patch("cs703.data.collect.violations.fetch_monthly_counts")
@patch("cs703.data.collect.violations.fetch_borough_counts")
def test_run_collection_writes_files_and_manifest(
    mock_borough,
    mock_monthly,
    mock_dow,
    mock_top_codes,
    mock_sample,
    mock_meters,
    mock_precincts,
    mock_weather,
    tmp_path,
):
    mock_borough.return_value = [{"violation_county": "NY", "count": "10"}]
    mock_monthly.return_value = [{"month": "2025-07-01T00:00:00.000", "count": "5"}]
    mock_dow.return_value = [{"dow": "1", "count": "3"}]
    mock_top_codes.return_value = [{"violation_code": "21", "count": "9"}]
    mock_sample.return_value = [{"issue_date": "2025-07-01T00:00:00.000", "violation_time": "0225P"}]
    mock_meters.return_value = [{"meter_number": "1"}]
    mock_precincts.return_value = [{"precinct": "1", "the_geom": {"type": "Polygon", "coordinates": []}}]
    mock_weather.return_value = {"hourly": {"time": ["2025-07-01T00:00"], "temperature_2m": [20.0], "precipitation": [0.0]}}

    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    raw_dir.mkdir()
    processed_dir.mkdir()

    manifest = run_collection(raw_dir, processed_dir, app_token=None)

    assert (raw_dir / "violations_sample_fy2026.csv").exists()
    assert (raw_dir / "parking_meters.csv").exists()
    assert (raw_dir / "nypd_precincts.geojson").exists()
    assert (raw_dir / "weather_fy2026.csv").exists()
    assert (processed_dir / "violations_by_borough.csv").exists()
    assert (processed_dir / "violations_by_month.csv").exists()
    assert (processed_dir / "violations_by_dow.csv").exists()
    assert (processed_dir / "violations_top_codes.csv").exists()

    manifest_path = processed_dir / "collection_manifest.json"
    assert manifest_path.exists()
    saved_manifest = json.loads(manifest_path.read_text())
    assert saved_manifest == manifest
    assert manifest["sources"]["violations_sample"]["rows_collected"] == 1
    assert manifest["sources"]["meters"]["rows_collected"] == 1
    assert manifest["sources"]["precincts"]["rows_collected"] == 1
    assert manifest["sources"]["weather"]["rows_collected"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/data/test_collect.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'cs703.data.collect'`

- [ ] **Step 3: Write the implementation**

```python
# src/cs703/data/collect.py
"""Orchestrates all Phase 2 fetchers into data/raw, data/processed, and a manifest."""

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from cs703.data import meters, precincts, violations, weather

WEATHER_START = "2025-07-01"
WEATHER_END = "2026-06-30"


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_weather_csv(path: Path, hourly: dict) -> int:
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    precip = hourly.get("precipitation", [])
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["time", "temperature_2m", "precipitation"])
        for row in zip(times, temps, precip):
            writer.writerow(row)
    return len(times)


def _write_geojson(path: Path, rows: list[dict]) -> None:
    features = []
    for row in rows:
        geometry = row.pop("the_geom", None)
        features.append({"type": "Feature", "geometry": geometry, "properties": row})
    path.write_text(json.dumps({"type": "FeatureCollection", "features": features}))


def run_collection(raw_dir: Path, processed_dir: Path, app_token: str | None = None) -> dict:
    borough_counts = violations.fetch_borough_counts(app_token=app_token)
    monthly_counts = violations.fetch_monthly_counts(app_token=app_token)
    dow_counts = violations.fetch_day_of_week_counts(app_token=app_token)
    top_codes = violations.fetch_top_violation_codes(app_token=app_token)
    sample_rows = violations.fetch_sample(app_token=app_token)
    meter_rows = meters.fetch_meters(app_token=app_token)
    precinct_rows = precincts.fetch_precincts(app_token=app_token)
    weather_body = weather.fetch_weather(WEATHER_START, WEATHER_END)

    _write_csv(processed_dir / "violations_by_borough.csv", borough_counts)
    _write_csv(processed_dir / "violations_by_month.csv", monthly_counts)
    _write_csv(processed_dir / "violations_by_dow.csv", dow_counts)
    _write_csv(processed_dir / "violations_top_codes.csv", top_codes)
    _write_csv(raw_dir / "violations_sample_fy2026.csv", sample_rows)
    _write_csv(raw_dir / "parking_meters.csv", meter_rows)
    _write_geojson(raw_dir / "nypd_precincts.geojson", precinct_rows)
    weather_rows = _write_weather_csv(raw_dir / "weather_fy2026.csv", weather_body.get("hourly", {}))

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": {
            "violations_aggregates": {
                "resource_id": violations.RESOURCE_ID,
                "files": [
                    "data/processed/violations_by_borough.csv",
                    "data/processed/violations_by_month.csv",
                    "data/processed/violations_by_dow.csv",
                    "data/processed/violations_top_codes.csv",
                ],
            },
            "violations_sample": {
                "resource_id": violations.RESOURCE_ID,
                "rows_collected": len(sample_rows),
                "file": "data/raw/violations_sample_fy2026.csv",
            },
            "meters": {
                "resource_id": meters.RESOURCE_ID,
                "rows_collected": len(meter_rows),
                "file": "data/raw/parking_meters.csv",
            },
            "precincts": {
                "resource_id": precincts.RESOURCE_ID,
                "rows_collected": len(precinct_rows),
                "file": "data/raw/nypd_precincts.geojson",
            },
            "weather": {
                "source": "open-meteo archive API",
                "date_range": [WEATHER_START, WEATHER_END],
                "rows_collected": weather_rows,
                "file": "data/raw/weather_fy2026.csv",
            },
        },
    }
    (processed_dir / "collection_manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest
```

```python
# scripts/collect_data.py
"""CLI entry point: `uv run python scripts/collect_data.py`"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cs703.config import DATA_RAW_DIR, DATA_PROCESSED_DIR, SOCRATA_APP_TOKEN
from cs703.data.collect import run_collection

if __name__ == "__main__":
    manifest = run_collection(DATA_RAW_DIR, DATA_PROCESSED_DIR, app_token=SOCRATA_APP_TOKEN)
    print(json.dumps(manifest, indent=2))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/data/test_collect.py -v`
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add src/cs703/data/collect.py scripts/collect_data.py tests/data/test_collect.py
git commit -m "feat: add collection orchestration script and manifest output"
```

---

### Task 8: Run the full test suite, then run the real collection

**Files:** none created; this task executes what Tasks 1–7 built.

- [ ] **Step 1: Run the entire test suite**

Run: `uv run pytest tests/ -v`
Expected: all tests pass (19 tests: 4 socrata_client + 5 violations + 2 meters/precincts + 1 weather + 6 analysis + 1 collect)

- [ ] **Step 2: Run the real data collection against live APIs**

Run: `uv run python scripts/collect_data.py`
Expected: takes roughly 4-6 minutes (dominated by the 1,000,000-row violations sample at ~50,000 rows/12s). Prints the manifest JSON at the end. Verify no exceptions.

- [ ] **Step 3: Spot-check the output files exist and are non-empty**

Run: `ls -la data/raw/ data/processed/ && wc -l data/raw/violations_sample_fy2026.csv data/raw/parking_meters.csv data/raw/weather_fy2026.csv`
Expected: `violations_sample_fy2026.csv` has ~1,000,001 lines (header + rows), `parking_meters.csv` has ~15,599 lines, `weather_fy2026.csv` has ~8,761 lines.

- [ ] **Step 4: Commit the manifest (not the raw/processed data itself, which stays gitignored)**

```bash
git status
```
Confirm `data/raw/*` and `data/processed/*` do not appear as untracked (they're gitignored per the scaffold design) — nothing to commit from this step. If `collection_manifest.json` or similar is unexpectedly untracked, check `.gitignore` covers `data/processed/*` before proceeding.

---

### Task 9: Compute report statistics and write `docs/phase2-data-understanding.md`

**Files:**
- Create: `docs/phase2-data-understanding.md`

This task has no automated test — it is a data-analysis-then-write task. Use a throwaway Python REPL (`uv run python`) or a short inline script to compute each number below from the real files produced in Task 8, then transcribe the results into the report. Do not fabricate any number; if a command produces something different from what's sketched here, use the real output.

- [ ] **Step 1: Load the manifest and the collected files for analysis**

```python
import json
import csv
from pathlib import Path
from cs703.data.analysis import hour_of_day_distribution, null_rates, duplicate_count, value_counts

manifest = json.loads(Path("data/processed/collection_manifest.json").read_text())

with open("data/raw/violations_sample_fy2026.csv") as f:
    sample_rows = list(csv.DictReader(f))

with open("data/raw/parking_meters.csv") as f:
    meter_rows = list(csv.DictReader(f))
```

- [ ] **Step 2: Compute Data Description Report numbers**

For each of the 5 collected files, compute: row count (`len(rows)` or `len(sample_rows)`), column list (`list(sample_rows[0].keys())`), file size (`Path(...).stat().st_size`). Use `manifest["sources"]` for resource ids and declared row counts, and cross-check against `len(...)` on the actual loaded rows.

- [ ] **Step 3: Compute Data Exploration Report numbers**

```python
hour_dist = hour_of_day_distribution([r["violation_time"] for r in sample_rows])
borough_dist = value_counts(sample_rows, "violation_county")
```
Also read `data/processed/violations_by_borough.csv`, `violations_by_month.csv`, `violations_by_dow.csv`, `violations_top_codes.csv` directly (full-population numbers) for the borough/month/day-of-week/top-codes tables — these are more authoritative than the 1M-row sample since they're server-side aggregates over all 15.69M rows.

- [ ] **Step 4: Compute Data Quality Report numbers**

```python
nulls = null_rates(sample_rows, ["issue_date", "violation_time", "violation_county", "violation_precinct", "violation_code", "street_name"])
dupes = duplicate_count(sample_rows, ["issue_date", "violation_time", "violation_county", "violation_precinct", "violation_code", "street_name"])
precinct_zero_count = sum(1 for r in sample_rows if r["violation_precinct"] == "0")
borough_codes_seen = value_counts(sample_rows, "violation_county")
```
Note any borough code outside the expected set `{"NY", "BX", "K", "Q", "R"}` as a data quality finding (document the exact codes actually observed — common real-world noise in this dataset includes blank, "ST", or other non-standard values).

- [ ] **Step 5: Write `docs/phase2-data-understanding.md`**

Structure (matching the design doc):

```markdown
# CS703 Phase 2: Data Understanding

Chen-Wei Weng
Date: 2026-10-02

## Task 2.1 — Data Collection Report
[sources table, known gap (ASP calendar), reproduction command]

## Task 2.2 — Data Description Report
[per-dataset schema table, row counts, file sizes, date ranges]

## Task 2.3 — Data Exploration Report
[borough table, monthly table, day-of-week table, hour-of-day table, top violation codes table, meters-by-borough table, weather monthly summary table]

## Task 2.4 — Data Quality Report
[null rates table, duplicate count, precinct=0 count, borough code anomalies, ASP calendar gap recorded formally, issue log table]
```

Fill every table with the real numbers computed in Steps 1–4. Use the exact prose style of `docs/phase1-business-understanding.md` (plain section headers, Markdown tables, no code fences in the final doc except where quoting a command).

- [ ] **Step 6: Commit**

```bash
git add docs/phase2-data-understanding.md
git commit -m "docs: add Phase 2 data understanding report"
```

---

### Task 10: Push to GitHub

- [ ] **Step 1: Push all commits from Tasks 1–9**

```bash
git push origin main
```

- [ ] **Step 2: Verify**

```bash
git log origin/main --oneline -12
```
Expected: all commits from this plan appear in `origin/main`.
