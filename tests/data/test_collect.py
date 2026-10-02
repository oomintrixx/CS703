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


@patch("cs703.data.collect.weather.fetch_weather")
@patch("cs703.data.collect.precincts.fetch_precincts")
@patch("cs703.data.collect.meters.fetch_meters")
@patch("cs703.data.collect.violations.fetch_sample")
@patch("cs703.data.collect.violations.fetch_top_violation_codes")
@patch("cs703.data.collect.violations.fetch_day_of_week_counts")
@patch("cs703.data.collect.violations.fetch_monthly_counts")
@patch("cs703.data.collect.violations.fetch_borough_counts")
def test_run_collection_handles_rows_with_heterogeneous_keys(
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
    # Second row has an extra key not present on the first row -- this is what
    # crashed the real collection run against live Socrata data.
    mock_meters.return_value = [
        {"meter_number": "1"},
        {"meter_number": "2", "parking_facility_name": "Some Garage"},
    ]
    mock_precincts.return_value = [{"precinct": "1", "the_geom": {"type": "Polygon", "coordinates": []}}]
    mock_weather.return_value = {"hourly": {"time": ["2025-07-01T00:00"], "temperature_2m": [20.0], "precipitation": [0.0]}}

    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    raw_dir.mkdir()
    processed_dir.mkdir()

    manifest = run_collection(raw_dir, processed_dir, app_token=None)

    assert manifest["sources"]["meters"]["rows_collected"] == 2
    meters_csv = (raw_dir / "parking_meters.csv").read_text()
    assert "parking_facility_name" in meters_csv
    assert "Some Garage" in meters_csv
