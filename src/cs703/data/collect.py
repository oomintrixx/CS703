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
    fieldnames = list(dict.fromkeys(key for row in rows for key in row.keys()))
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, restval="")
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


def _socrata_source_url(resource_id: str) -> str:
    return f"https://data.cityofnewyork.us/resource/{resource_id}.json"


def run_collection(raw_dir: Path, processed_dir: Path, app_token: str | None = None) -> dict:
    sources: dict = {}

    # (a) violations aggregates: fetch all 4, then write all 4.
    borough_counts = violations.fetch_borough_counts(app_token=app_token)
    monthly_counts = violations.fetch_monthly_counts(app_token=app_token)
    dow_counts = violations.fetch_day_of_week_counts(app_token=app_token)
    top_codes = violations.fetch_top_violation_codes(app_token=app_token)

    borough_path = processed_dir / "violations_by_borough.csv"
    monthly_path = processed_dir / "violations_by_month.csv"
    dow_path = processed_dir / "violations_by_dow.csv"
    top_codes_path = processed_dir / "violations_top_codes.csv"
    _write_csv(borough_path, borough_counts)
    _write_csv(monthly_path, monthly_counts)
    _write_csv(dow_path, dow_counts)
    _write_csv(top_codes_path, top_codes)
    aggregates_fetched_at = datetime.now(timezone.utc).isoformat()

    aggregate_files = {
        "data/processed/violations_by_borough.csv": borough_path,
        "data/processed/violations_by_month.csv": monthly_path,
        "data/processed/violations_by_dow.csv": dow_path,
        "data/processed/violations_top_codes.csv": top_codes_path,
    }
    sources["violations_aggregates"] = {
        "resource_id": violations.RESOURCE_ID,
        "rows_collected": sum(int(row["count"]) for row in borough_counts),
        "files": list(aggregate_files.keys()),
        "file_size_bytes": {name: path.stat().st_size for name, path in aggregate_files.items()},
        "fetched_at": aggregates_fetched_at,
        "source_url": _socrata_source_url(violations.RESOURCE_ID),
    }

    # (b) violations sample: fetch, then write.
    sample_rows = violations.fetch_sample(app_token=app_token)
    sample_path = raw_dir / "violations_sample_fy2026.csv"
    _write_csv(sample_path, sample_rows)
    sources["violations_sample"] = {
        "resource_id": violations.RESOURCE_ID,
        "rows_collected": len(sample_rows),
        "file": "data/raw/violations_sample_fy2026.csv",
        "file_size_bytes": sample_path.stat().st_size,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source_url": _socrata_source_url(violations.RESOURCE_ID),
    }

    # (c) meters: fetch, then write.
    meter_rows = meters.fetch_meters(app_token=app_token)
    meters_path = raw_dir / "parking_meters.csv"
    _write_csv(meters_path, meter_rows)
    sources["meters"] = {
        "resource_id": meters.RESOURCE_ID,
        "rows_collected": len(meter_rows),
        "file": "data/raw/parking_meters.csv",
        "file_size_bytes": meters_path.stat().st_size,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source_url": _socrata_source_url(meters.RESOURCE_ID),
    }

    # (d) precincts: fetch, then write.
    precinct_rows = precincts.fetch_precincts(app_token=app_token)
    precincts_path = raw_dir / "nypd_precincts.geojson"
    _write_geojson(precincts_path, precinct_rows)
    sources["precincts"] = {
        "resource_id": precincts.RESOURCE_ID,
        "rows_collected": len(precinct_rows),
        "file": "data/raw/nypd_precincts.geojson",
        "file_size_bytes": precincts_path.stat().st_size,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source_url": _socrata_source_url(precincts.RESOURCE_ID),
    }

    # (e) weather: fetch, then write.
    weather_body = weather.fetch_weather(WEATHER_START, WEATHER_END)
    weather_fetched_at = datetime.now(timezone.utc).isoformat()
    weather_path = raw_dir / "weather_fy2026.csv"
    weather_rows = _write_weather_csv(weather_path, weather_body.get("hourly", {}))
    sources["weather"] = {
        "source": "open-meteo archive API",
        "date_range": [WEATHER_START, WEATHER_END],
        "rows_collected": weather_rows,
        "file": "data/raw/weather_fy2026.csv",
        "file_size_bytes": weather_path.stat().st_size,
        "fetched_at": weather_fetched_at,
        "source_url": "https://archive-api.open-meteo.com/v1/archive",
    }

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": sources,
    }
    (processed_dir / "collection_manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest
