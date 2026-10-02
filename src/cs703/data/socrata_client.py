"""Thin pagination client for NYC Open Data (Socrata) resources."""

import time

import requests

_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


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
    max_retries: int = 5,
    backoff_base: float = 2.0,
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

        attempt = 0
        while True:
            try:
                response = requests.get(url, params=params, timeout=90)
                response.raise_for_status()
                page = response.json()
                break
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                if attempt >= max_retries:
                    raise
                time.sleep(backoff_base**attempt)
                attempt += 1
            except requests.exceptions.HTTPError as exc:
                status_code = exc.response.status_code if exc.response is not None else None
                if status_code not in _RETRYABLE_STATUS_CODES or attempt >= max_retries:
                    raise
                time.sleep(backoff_base**attempt)
                attempt += 1

        rows.extend(page)

        if max_rows is not None and len(rows) >= max_rows:
            return rows[:max_rows]
        if len(page) < page_size:
            return rows

        offset += page_size
