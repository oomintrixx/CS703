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
