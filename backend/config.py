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
