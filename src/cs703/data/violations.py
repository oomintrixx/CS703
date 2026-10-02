"""Fetchers for the FY2026 Parking Violations Issued dataset."""

from cs703.data.socrata_client import fetch_all

RESOURCE_ID = "9mwx-gamw"

SAMPLE_COLUMNS = (
    "issue_date, violation_time, violation_county, violation_precinct, "
    "violation_code, plate_type, street_name"
)


def fetch_borough_counts(app_token=None) -> list[dict]:
    return fetch_all(
        RESOURCE_ID,
        select="violation_county, count(*)",
        group="violation_county",
        order="count(*) DESC",
        app_token=app_token,
    )


def fetch_monthly_counts(app_token=None) -> list[dict]:
    return fetch_all(
        RESOURCE_ID,
        select="date_trunc_ym(issue_date) as month, count(*)",
        group="month",
        order="month",
        app_token=app_token,
    )


def fetch_day_of_week_counts(app_token=None) -> list[dict]:
    return fetch_all(
        RESOURCE_ID,
        select="date_extract_dow(issue_date) as dow, count(*)",
        group="dow",
        order="dow",
        app_token=app_token,
    )


def fetch_top_violation_codes(limit: int = 15, app_token=None) -> list[dict]:
    return fetch_all(
        RESOURCE_ID,
        select="violation_code, count(*)",
        group="violation_code",
        order="count(*) DESC",
        max_rows=limit,
        app_token=app_token,
    )


def fetch_sample(n: int = 1_000_000, app_token=None) -> list[dict]:
    return fetch_all(
        RESOURCE_ID,
        select=SAMPLE_COLUMNS,
        max_rows=n,
        app_token=app_token,
    )
