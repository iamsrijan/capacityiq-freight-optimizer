from __future__ import annotations

import csv
from collections import defaultdict
from typing import Any

from config import DATA_DIR
from utils import as_float, as_int


def read_csv_table(name: str) -> list[dict[str, str]]:
    path = DATA_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing data file: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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


def dataset_summary(dataset: dict[str, Any] = DATASET) -> dict[str, Any]:
    counts = dataset["rawCounts"]
    return {
        **counts,
        "api": "CapacityIQ local backend",
        "dataDirectory": "backend/data",
        "totalCapacityTonnes": sum(
            as_int(mode["capacity"])
            for corridor in dataset["corridors"]
            for mode in corridor["modes"]
        ),
    }


def find_corridor(corridor_id: str, dataset: dict[str, Any] = DATASET) -> dict[str, Any] | None:
    for corridor in dataset["corridors"]:
        if corridor["id"] == corridor_id:
            return corridor
    return None
