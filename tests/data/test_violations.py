# tests/data/test_violations.py
from unittest.mock import patch

from cs703.data import violations


@patch("cs703.data.violations.fetch_all")
def test_fetch_borough_counts_groups_by_county(mock_fetch_all):
    mock_fetch_all.return_value = [{"violation_county": "NY", "count": "100"}]

    result = violations.fetch_borough_counts()

    assert result == [{"violation_county": "NY", "count": "100"}]
    _, kwargs = mock_fetch_all.call_args
    assert mock_fetch_all.call_args.args[0] == violations.RESOURCE_ID
    assert kwargs["group"] == "violation_county"
    assert kwargs["select"] == "violation_county, count(*)"


@patch("cs703.data.violations.fetch_all")
def test_fetch_monthly_counts_groups_by_month(mock_fetch_all):
    mock_fetch_all.return_value = []

    violations.fetch_monthly_counts()

    kwargs = mock_fetch_all.call_args.kwargs
    assert kwargs["group"] == "month"
    assert kwargs["select"] == "date_trunc_ym(issue_date) as month, count(*)"
    assert kwargs["order"] == "month"


@patch("cs703.data.violations.fetch_all")
def test_fetch_day_of_week_counts_groups_by_dow(mock_fetch_all):
    mock_fetch_all.return_value = []

    violations.fetch_day_of_week_counts()

    kwargs = mock_fetch_all.call_args.kwargs
    assert kwargs["group"] == "dow"
    assert kwargs["select"] == "date_extract_dow(issue_date) as dow, count(*)"


@patch("cs703.data.violations.fetch_all")
def test_fetch_top_violation_codes_orders_desc_with_limit(mock_fetch_all):
    mock_fetch_all.return_value = []

    violations.fetch_top_violation_codes(limit=15)

    args, kwargs = mock_fetch_all.call_args
    assert kwargs["group"] == "violation_code"
    assert kwargs["order"] == "count(*) DESC"
    assert kwargs["max_rows"] == 15


@patch("cs703.data.violations.fetch_all")
def test_fetch_sample_requests_selected_columns_and_row_cap(mock_fetch_all):
    mock_fetch_all.return_value = []

    violations.fetch_sample(n=1_000_000)

    kwargs = mock_fetch_all.call_args.kwargs
    assert kwargs["max_rows"] == 1_000_000
    assert "issue_date" in kwargs["select"]
    assert "violation_time" in kwargs["select"]
    assert "violation_county" in kwargs["select"]
    assert "violation_precinct" in kwargs["select"]
    assert "violation_code" in kwargs["select"]
