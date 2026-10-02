from cs703.data.analysis import (
    parse_violation_time_to_hour,
    hour_of_day_distribution,
    null_rates,
    duplicate_count,
    value_counts,
)


def test_parse_violation_time_to_hour_handles_am_pm():
    assert parse_violation_time_to_hour("0225P") == 14
    assert parse_violation_time_to_hour("1130A") == 11
    assert parse_violation_time_to_hour("1200A") == 0
    assert parse_violation_time_to_hour("1200P") == 12


def test_parse_violation_time_to_hour_handles_invalid_input():
    assert parse_violation_time_to_hour("") is None
    assert parse_violation_time_to_hour(None) is None
    assert parse_violation_time_to_hour("garbage") is None


def test_hour_of_day_distribution_counts_buckets():
    times = ["0225P", "0225P", "1130A", ""]
    result = hour_of_day_distribution(times)
    assert result == {14: 2, 11: 1}


def test_null_rates_computes_fraction_missing_or_empty():
    rows = [{"a": "1", "b": ""}, {"a": None, "b": "2"}, {"a": "3", "b": "4"}]
    result = null_rates(rows, ["a", "b"])
    assert result == {"a": 1 / 3, "b": 1 / 3}


def test_duplicate_count_counts_rows_sharing_key():
    rows = [
        {"id": "1", "v": "x"},
        {"id": "1", "v": "x"},
        {"id": "2", "v": "y"},
    ]
    assert duplicate_count(rows, ["id", "v"]) == 1


def test_value_counts_tallies_column():
    rows = [{"county": "NY"}, {"county": "NY"}, {"county": "BX"}]
    assert value_counts(rows, "county") == {"NY": 2, "BX": 1}
