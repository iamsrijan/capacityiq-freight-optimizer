from __future__ import annotations

from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent / "data"

COMPATIBILITY_FIT = {
    "ambient": 1.0,
    "dry": 1.0,
    "fragile": 0.86,
    "regulated": 0.74,
    "chilled": 0.42,
}

# Operating target by mode. The optimiser keeps the rest as a realistic buffer
# for slot risk, loading variance, exceptions, and service reliability.
MODE_TARGET_FILL = {
    "road": 0.93,
    "air": 0.84,
    "sea": 0.78,
    "staging": 0.88,
}

CARGO_FAMILY_FIT = {
    "food-grade dry": 1.0,
    "chilled food": 0.88,
    "fresh produce": 0.82,
    "textile dry": 0.84,
    "container export": 0.78,
    "parcel returns": 0.74,
    "electronics": 0.72,
    "fragile craft": 0.7,
    "secured samples": 0.66,
    "regulated pharma": 0.62,
    "regulated devices": 0.62,
}

CONTRACT_FIT = {
    "dedicated fleet": 1.0,
    "fixed monthly": 0.94,
    "SLA contract": 0.92,
    "per-tonne contract": 0.84,
    "per-trip contract": 0.78,
    "spot market": 0.68,
}

API_ENDPOINTS = [
    "/api/health",
    "/api/corridors",
    "/api/corridors/{id}",
    "/api/shipments?corridor_id=northeast&limit=50",
    "/api/capacity?corridor_id=northeast",
    "/api/retail-profiles",
    "/api/hubs",
    "/api/partners",
    "/api/tables",
    "/api/optimise",
]
