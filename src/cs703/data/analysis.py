"""Pure, network-free helpers for the Phase 2 description/exploration/quality report."""

from collections import Counter


def parse_violation_time_to_hour(value: str | None) -> int | None:
    if not value or len(value) != 5:
        return None
    digits, suffix = value[:4], value[4]
    if not digits.isdigit() or suffix not in ("A", "P"):
        return None
    hour = int(digits[:2])
    if hour == 12:
        hour = 0
    if suffix == "P":
        hour += 12
    if not (0 <= hour <= 23):
        return None
    return hour


def hour_of_day_distribution(times: list[str]) -> dict[int, int]:
    counts: Counter[int] = Counter()
    for value in times:
        hour = parse_violation_time_to_hour(value)
        if hour is not None:
            counts[hour] += 1
    return dict(counts)


def null_rates(rows: list[dict], columns: list[str]) -> dict[str, float]:
    total = len(rows)
    result = {}
    for column in columns:
        missing = sum(1 for row in rows if not row.get(column))
        result[column] = missing / total if total else 0.0
    return result


def duplicate_count(rows: list[dict], key_columns: list[str]) -> int:
    seen: Counter[tuple] = Counter()
    for row in rows:
        key = tuple(row.get(column) for column in key_columns)
        seen[key] += 1
    return sum(count - 1 for count in seen.values() if count > 1)


def value_counts(rows: list[dict], column: str) -> dict[str, int]:
    return dict(Counter(row.get(column) for row in rows))
