"""Fetcher for NYC historical hourly weather via the Open-Meteo archive API."""

import time

import requests

NYC_LAT = 40.7829
NYC_LON = -73.9654
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


def fetch_weather(start_date: str, end_date: str, max_retries: int = 5) -> dict:
    params = {
        "latitude": NYC_LAT,
        "longitude": NYC_LON,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "temperature_2m,precipitation",
        "timezone": "America/New_York",
    }

    attempt = 0
    while True:
        try:
            response = requests.get(ARCHIVE_URL, params=params, timeout=90)
            response.raise_for_status()
            return response.json()
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            if attempt >= max_retries:
                raise
            time.sleep(2.0**attempt)
            attempt += 1
