"""Fetcher for the NYPD Police Precincts boundary dataset."""

from cs703.data.socrata_client import fetch_all

RESOURCE_ID = "y76i-bdw7"


def fetch_precincts(app_token=None) -> list[dict]:
    return fetch_all(RESOURCE_ID, app_token=app_token)
