from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(__file__).resolve().parent / "data"
COMPATIBILITY_FIT = {
    "ambient": 1.0,
    "dry": 1.0,
    "fragile": 0.86,
    "regulated": 0.74,
    "chilled": 0.42,
}


def read_csv_table(name: str) -> list[dict[str, str]]:
    path = DATA_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing data file: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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


def load_dataset() -> dict[str, Any]:
    corridors_raw = read_csv_table("corridors.csv")
    capacity_raw = read_csv_table("capacity.csv")
    shipments_raw = read_csv_table("shipments.csv")
    retail_raw = read_csv_table("retail_profiles.csv")
    retail_assortments_raw = read_csv_table("retail_assortments.csv")
    hubs_raw = read_csv_table("hubs.csv")
    partners_raw = read_csv_table("partners.csv")

    capacity_by_corridor: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in capacity_raw:
        capacity_by_corridor[row["corridor_id"]].append(
            {
                "mode": row["mode"],
                "label": row["label"],
                "capacity": as_int(row["capacity_tonnes"]),
                "available": as_int(row["available_percent"]),
                "status": row["status"],
            }
        )

    shipments_by_corridor: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in shipments_raw:
        shipments_by_corridor[row["corridor_id"]].append(
            {
                "id": row["id"],
                "shipper": row["shipper"],
                "cargo": row["cargo"],
                "origin": row["origin"],
                "destination": row["destination"],
                "tonnes": as_int(row["tonnes"]),
                "mode": row["mode"],
                "revenuePerTon": as_int(row["revenue_per_ton"]),
                "detourKm": as_int(row["detour_km"]),
                "reliability": as_int(row["reliability"]),
                "compatibility": row["compatibility"],
                "window": row["window"],
                "urgency": as_int(row["urgency"]),
                "priority": row["priority"],
                "pickupWindow": row["pickup_window"],
                "deliveryWindow": row["delivery_window"],
            }
        )

    corridors: list[dict[str, Any]] = []
    for row in corridors_raw:
        corridor_id = row["id"]
        corridors.append(
            {
                "id": corridor_id,
                "name": row["name"],
                "anchor": row["anchor"],
                "origin": row["origin"],
                "destination": row["destination"],
                "returnLane": row["return_lane"],
                "recurring": row["recurring"],
                "distanceKm": as_int(row["distance_km"]),
                "baselineEmptyKm": as_int(row["baseline_empty_km"]),
                "baseAnchorTonnes": as_int(row["base_anchor_tonnes"]),
                "vehicles": as_int(row["vehicles"]),
                "serviceLevel": as_int(row["service_level"]),
                "region": row["region"],
                "modes": capacity_by_corridor[corridor_id],
                "shipments": shipments_by_corridor[corridor_id],
            }
        )

    assortments_by_retail: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in retail_assortments_raw:
        assortments_by_retail[row["retail_id"]].append(
            {
                "label": row["label"],
                "share": as_int(row["share"]),
                "uplift": as_int(row["uplift"]),
            }
        )

    retail_profiles = [
        {
            "id": row["id"],
            "name": row["name"],
            "terminal": row["terminal"],
            "passengerMix": row["passenger_mix"],
            "weeklyFlights": as_int(row["weekly_flights"]),
            "baseRevenue": as_int(row["base_revenue"]),
            "compliance": row["compliance"],
            "assortments": assortments_by_retail[row["id"]],
        }
        for row in retail_raw
    ]

    hubs = [
        {
            "id": row["id"],
            "name": row["name"],
            "city": row["city"],
            "state": row["state"],
            "modes": row["modes"].split("|"),
            "dockDoors": as_int(row["dock_doors"]),
            "stagingTonnes": as_int(row["staging_tonnes"]),
            "coldCapacityTonnes": as_int(row["cold_capacity_tonnes"]),
            "reliability": as_int(row["reliability"]),
        }
        for row in hubs_raw
    ]

    partners = [
        {
            "id": row["id"],
            "name": row["name"],
            "type": row["type"],
            "homeRegion": row["home_region"],
            "modes": row["modes"].split("|"),
            "fleetSize": as_int(row["fleet_size"]),
            "onTimePercent": as_int(row["on_time_percent"]),
            "cancellationRatePercent": as_float(row["cancellation_rate_percent"]),
            "claimsRatePercent": as_float(row["claims_rate_percent"]),
        }
        for row in partners_raw
    ]

    return {
        "corridors": corridors,
        "retailProfiles": retail_profiles,
        "hubs": hubs,
        "partners": partners,
        "rawCounts": {
            "corridors": len(corridors_raw),
            "capacityRows": len(capacity_raw),
            "shipments": len(shipments_raw),
            "retailProfiles": len(retail_raw),
            "retailAssortments": len(retail_assortments_raw),
            "hubs": len(hubs_raw),
            "partners": len(partners_raw),
        },
    }


DATASET = load_dataset()


def score_shipment(
    shipment: dict[str, Any],
    max_detour: int,
    guardrail: int,
) -> int:
    route_fit = max(0, 1 - as_int(shipment["detourKm"]) / max(max_detour, 1))
    reliability_fit = as_int(shipment["reliability"]) / 100
    revenue_fit = min(as_int(shipment["revenuePerTon"]) / 12000, 1)
    urgency_fit = as_int(shipment["urgency"]) / 100
    compatibility_fit = COMPATIBILITY_FIT.get(str(shipment["compatibility"]), 0.5)
    guardrail_penalty = ((guardrail - 50) / 50) * (1 - compatibility_fit) * 22

    return round(
        route_fit * 32
        + reliability_fit * 24
        + compatibility_fit * 22
        + revenue_fit * 15
        + urgency_fit * 7
        - guardrail_penalty
    )


def optimise_corridor(
    corridor: dict[str, Any],
    anchor_enabled: bool,
    anchor_multiplier: float,
    max_detour: int,
    guardrail: int,
) -> dict[str, Any]:
    anchor_factor = anchor_multiplier if anchor_enabled else 0.54
    remaining: dict[str, int] = {}

    for item in corridor["modes"]:
        available_capacity = round(as_int(item["capacity"]) * (as_int(item["available"]) / 100) * anchor_factor)
        remaining[item["mode"]] = available_capacity

    scored = []
    for shipment in corridor["shipments"]:
        scored.append(
            {
                **shipment,
                "score": score_shipment(shipment, max_detour, guardrail),
                "matchedTonnes": 0,
                "reason": "",
            }
        )
    scored.sort(key=lambda item: item["score"], reverse=True)

    accepted: list[dict[str, Any]] = []
    declined: list[dict[str, Any]] = []
    threshold = max(55, guardrail - 12)

    for shipment in scored:
        mode = shipment["mode"]
        mode_remaining = remaining.get(mode, 0)
        incompatible = guardrail >= 82 and shipment["compatibility"] in {"chilled", "regulated"}
        detour_blocked = shipment["mode"] != "air" and as_int(shipment["detourKm"]) > max_detour

        if mode_remaining <= 0:
            declined.append({**shipment, "reason": "No capacity left in this mode"})
            continue

        if detour_blocked:
            declined.append({**shipment, "reason": "Detour exceeds lane policy"})
            continue

        if shipment["score"] < threshold or incompatible:
            declined.append({**shipment, "reason": "Guardrail confidence too low"})
            continue

        matched_tonnes = min(as_int(shipment["tonnes"]), mode_remaining)
        remaining[mode] = mode_remaining - matched_tonnes
        accepted.append(
            {
                **shipment,
                "matchedTonnes": matched_tonnes,
                "reason": "Full match"
                if matched_tonnes == as_int(shipment["tonnes"])
                else f"{matched_tonnes} t partial match",
            }
        )

    adjusted_capacity = sum(
        round(as_int(item["capacity"]) * (as_int(item["available"]) / 100) * anchor_factor)
        for item in corridor["modes"]
    )
    matched_tonnes = sum(as_int(item["matchedTonnes"]) for item in accepted)
    revenue = sum(as_int(item["matchedTonnes"]) * as_int(item["revenuePerTon"]) for item in accepted)
    empty_km_avoided = round(
        sum(
            (as_int(item["matchedTonnes"]) / (16 if item["mode"] == "road" else 24))
            * max(120, as_int(corridor["distanceKm"]) - as_int(item["detourKm"]))
            for item in accepted
        )
    )
    cost_saved = empty_km_avoided * 68
    load_factor = round((matched_tonnes / adjusted_capacity) * 100) if adjusted_capacity else 0
    baseline_load_factor = 19 if anchor_enabled else 11
    unit_cost_drop = max(0, min(34, round((load_factor - baseline_load_factor) * 0.62)))
    anchor_tonnes = round(as_int(corridor["baseAnchorTonnes"]) * anchor_factor)

    mode_utilisation = []
    for item in corridor["modes"]:
        available = round(as_int(item["capacity"]) * (as_int(item["available"]) / 100) * anchor_factor)
        mode_remaining = remaining.get(item["mode"], 0)
        used = max(0, available - mode_remaining)
        utilisation = round((used / available) * 100) if available else 0
        mode_utilisation.append(
            {
                **item,
                "availableTonnes": available,
                "remainingTonnes": mode_remaining,
                "usedTonnes": used,
                "utilisation": utilisation,
            }
        )

    return {
        "accepted": accepted,
        "declined": declined,
        "remaining": remaining,
        "modeUtilisation": mode_utilisation,
        "adjustedCapacity": adjusted_capacity,
        "matchedTonnes": matched_tonnes,
        "revenue": revenue,
        "emptyKmAvoided": empty_km_avoided,
        "costSaved": cost_saved,
        "loadFactor": load_factor,
        "unitCostDrop": unit_cost_drop,
        "anchorTonnes": anchor_tonnes,
    }


def dataset_summary() -> dict[str, Any]:
    counts = DATASET["rawCounts"]
    return {
        **counts,
        "api": "CapacityIQ local backend",
        "dataDirectory": "backend/data",
        "totalCapacityTonnes": sum(
            as_int(mode["capacity"])
            for corridor in DATASET["corridors"]
            for mode in corridor["modes"]
        ),
    }


def find_corridor(corridor_id: str) -> dict[str, Any] | None:
    for corridor in DATASET["corridors"]:
        if corridor["id"] == corridor_id:
            return corridor
    return None


def parse_limit(query: dict[str, list[str]], default: int = 100, maximum: int = 1000) -> int:
    return max(1, min(maximum, as_int(query.get("limit", [default])[0], default)))


def apply_limit(rows: list[dict[str, Any]], query: dict[str, list[str]]) -> list[dict[str, Any]]:
    offset = max(0, as_int(query.get("offset", [0])[0], 0))
    limit = parse_limit(query)
    return rows[offset : offset + limit]


class CapacityIQHandler(BaseHTTPRequestHandler):
    server_version = "CapacityIQLocalBackend/1.0"

    def _send_json(self, status: int, payload: Any) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(encoded)

    def do_OPTIONS(self) -> None:
        self._send_json(204, {})

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)

        if path in {"/", "/api", "/api/health"}:
            self._send_json(
                200,
                {
                    "status": "ok",
                    "service": "CapacityIQ local backend",
                    "dataset": dataset_summary(),
                    "endpoints": [
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
                    ],
                },
            )
            return

        if path == "/api/corridors":
            self._send_json(200, DATASET["corridors"])
            return

        if path.startswith("/api/corridors/"):
            corridor_id = unquote(path.removeprefix("/api/corridors/"))
            corridor = find_corridor(corridor_id)
            if corridor:
                self._send_json(200, corridor)
            else:
                self._send_json(404, {"error": f"Unknown corridor: {corridor_id}"})
            return

        if path == "/api/shipments":
            corridor_id = query.get("corridor_id", [""])[0]
            shipments = [
                shipment
                for corridor in DATASET["corridors"]
                if not corridor_id or corridor["id"] == corridor_id
                for shipment in corridor["shipments"]
            ]
            self._send_json(200, {"count": len(shipments), "rows": apply_limit(shipments, query)})
            return

        if path == "/api/capacity":
            corridor_id = query.get("corridor_id", [""])[0]
            capacity = [
                mode
                for corridor in DATASET["corridors"]
                if not corridor_id or corridor["id"] == corridor_id
                for mode in corridor["modes"]
            ]
            self._send_json(200, {"count": len(capacity), "rows": apply_limit(capacity, query)})
            return

        if path == "/api/retail-profiles":
            self._send_json(200, DATASET["retailProfiles"])
            return

        if path == "/api/hubs":
            self._send_json(200, {"count": len(DATASET["hubs"]), "rows": apply_limit(DATASET["hubs"], query)})
            return

        if path == "/api/partners":
            self._send_json(200, {"count": len(DATASET["partners"]), "rows": apply_limit(DATASET["partners"], query)})
            return

        if path == "/api/tables":
            self._send_json(200, dataset_summary())
            return

        self._send_json(404, {"error": f"Unknown endpoint: {path}"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        if path not in {"/api/optimise", "/api/optimize"}:
            self._send_json(404, {"error": f"Unknown endpoint: {path}"})
            return

        length = as_int(self.headers.get("Content-Length"), 0)
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Request body must be valid JSON"})
            return

        corridor_id = payload.get("corridorId") or payload.get("corridor_id") or "northeast"
        corridor = find_corridor(str(corridor_id))
        if not corridor:
            self._send_json(404, {"error": f"Unknown corridor: {corridor_id}"})
            return

        result = optimise_corridor(
            corridor,
            bool(payload.get("anchorEnabled", True)),
            as_float(payload.get("anchorMultiplier", 1), 1),
            as_int(payload.get("maxDetour", 120), 120),
            as_int(payload.get("guardrail", 74), 74),
        )
        self._send_json(200, {"corridor": corridor, "result": result})

    def log_message(self, format: str, *args: Any) -> None:
        if getattr(self.server, "quiet", False):
            return
        super().log_message(format, *args)


def run(host: str, port: int, quiet: bool = False) -> None:
    server = ThreadingHTTPServer((host, port), CapacityIQHandler)
    server.quiet = quiet  # type: ignore[attr-defined]
    print(f"CapacityIQ backend running at http://{host}:{port}")
    print(f"Loaded dataset: {json.dumps(dataset_summary(), indent=2)}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nCapacityIQ backend stopped")
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the CapacityIQ local backend API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    run(args.host, args.port, args.quiet)


if __name__ == "__main__":
    main()
