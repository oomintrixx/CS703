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
