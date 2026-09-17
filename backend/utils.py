from __future__ import annotations

from typing import Any


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_limit(query: dict[str, list[str]], default: int = 100, maximum: int = 1000) -> int:
    return max(1, min(maximum, as_int(query.get("limit", [default])[0], default)))


def apply_limit(rows: list[dict[str, Any]], query: dict[str, list[str]]) -> list[dict[str, Any]]:
    offset = max(0, as_int(query.get("offset", [0])[0], 0))
    limit = parse_limit(query)
    return rows[offset : offset + limit]
