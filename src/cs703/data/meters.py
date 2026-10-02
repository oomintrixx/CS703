"""Fetcher for the Parking Meters Locations and Status dataset."""

from cs703.data.socrata_client import fetch_all

RESOURCE_ID = "693u-uax6"


def fetch_meters(app_token=None) -> list[dict]:
    return fetch_all(RESOURCE_ID, app_token=app_token)
