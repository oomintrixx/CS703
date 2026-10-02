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
