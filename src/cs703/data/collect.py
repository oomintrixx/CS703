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
