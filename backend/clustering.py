from __future__ import annotations

from collections import defaultdict
from math import sqrt
from typing import Any

from config import CARGO_FAMILY_FIT
from utils import as_float, as_int


VectorRow = dict[str, Any]


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0


def standardise(rows: list[VectorRow], features: list[str]) -> list[list[float]]:
    columns = [[as_float(row["features"].get(feature)) for row in rows] for feature in features]
    stats = []
    for column in columns:
        avg = mean(column)
        variance = mean([(value - avg) ** 2 for value in column])
        stats.append((avg, sqrt(variance) or 1))

    vectors = []
    for row in rows:
        vectors.append(
            [
                (as_float(row["features"].get(feature)) - stats[index][0]) / stats[index][1]
                for index, feature in enumerate(features)
            ]
        )
    return vectors


def euclidean(first: list[float], second: list[float]) -> float:
    return sqrt(sum((first[index] - second[index]) ** 2 for index in range(len(first))))


def closest_centroid(vector: list[float], centroids: list[list[float]]) -> int:
    distances = [euclidean(vector, centroid) for centroid in centroids]
    return distances.index(min(distances))


def run_kmeans(rows: list[VectorRow], features: list[str], k: int, iterations: int = 28) -> list[int]:
    if not rows:
        return []

    k = max(1, min(k, len(rows)))
    vectors = standardise(rows, features)
    ordered_indices = sorted(range(len(vectors)), key=lambda index: sum(vectors[index]))
    if k == 1:
        centroids = [vectors[ordered_indices[len(ordered_indices) // 2]]]
    else:
        centroids = [
            vectors[ordered_indices[round(position * (len(ordered_indices) - 1) / (k - 1))]]
            for position in range(k)
        ]

    assignments = [0] * len(vectors)
    for _ in range(iterations):
        next_assignments = [closest_centroid(vector, centroids) for vector in vectors]
        if next_assignments == assignments:
            break
        assignments = next_assignments

        next_centroids = []
        for cluster_index in range(k):
            members = [
                vector for index, vector in enumerate(vectors) if assignments[index] == cluster_index
            ]
            if not members:
                next_centroids.append(centroids[cluster_index])
                continue
            next_centroids.append(
                [mean([member[feature_index] for member in members]) for feature_index in range(len(features))]
            )
        centroids = next_centroids

    return assignments


def cluster_label(domain: str, centroid: dict[str, float]) -> str:
    if domain == "routes":
        if centroid["distanceKm"] > 800 and centroid["totalCapacityTonnes"] > 2000:
            return "Long-haul high-capacity corridors"
        if centroid["distanceKm"] < 450:
            return "Short-cycle urban and regional loops"
        if centroid["baselineEmptyKm"] > 45000:
            return "High empty-kilometre exposure lanes"
        return "Balanced regional freight corridors"

    if domain == "customers":
        if centroid["avgRevenuePerTon"] > 11000:
            return "Premium urgent shippers"
        if centroid["regulatedShare"] > 35:
            return "Compliance-heavy customers"
        if centroid["shipmentCount"] > 14 and centroid["totalTonnes"] > 4000:
            return "High-volume recurring shippers"
        return "Flexible backhaul customers"

    if domain == "shipments":
        if centroid["revenuePerTon"] > 14000:
            return "High-value urgent cargo"
        if centroid["cargoFit"] < 0.7:
            return "Strict compatibility cargo"
        if centroid["tonnes"] > 500:
            return "Bulk consolidation loads"
        return "Standard compatible backhaul"

    if domain == "vehicles":
        if centroid["fleetSize"] > 120 and centroid["onTimePercent"] > 88:
            return "Large reliable fleet partners"
        if centroid["claimsRatePercent"] > 2:
            return "Claims-sensitive operators"
        if centroid["cancellationRatePercent"] > 5:
            return "Cancellation-risk capacity"
        return "Specialist flexible operators"

    if centroid["weeklyFlights"] > 100:
        return "High-frequency domestic passenger flows"
    if centroid["baseRevenue"] > 28000000:
        return "Premium long-haul retail flows"
    if centroid["weightedUplift"] > 12:
        return "High-uplift destination retail clusters"
    return "Destination-aware passenger cohorts"


def cluster_insight(domain: str, label: str) -> str:
    insights = {
        "Long-haul high-capacity corridors": "Use these lanes for large backhaul pools, multi-stop consolidation, and stronger marketplace liquidity.",
        "Short-cycle urban and regional loops": "Use fast dispatch waves, tighter route windows, and repeat vehicle assignment.",
        "High empty-kilometre exposure lanes": "Prioritise backhaul discovery and transporter monetisation before adding new assets.",
        "Balanced regional freight corridors": "Keep normal guardrails and use these lanes as reliable network fillers.",
        "Premium urgent shippers": "Route through air or high-reliability road capacity and protect clearance windows.",
        "Compliance-heavy customers": "Require regulated handling, verified custody, and stricter approval before execution.",
        "High-volume recurring shippers": "Treat as anchor-like demand for predictable capacity planning.",
        "Flexible backhaul customers": "Use for filling return capacity when core anchor demand leaves unused space.",
        "High-value urgent cargo": "Assign secure transport, high driver score, and fast handling paths.",
        "Strict compatibility cargo": "Separate from food-grade anchor loads unless compatibility rules explicitly allow it.",
        "Bulk consolidation loads": "Batch into sea, staging, or full truck moves instead of fragmenting capacity.",
        "Standard compatible backhaul": "Use as normal marketplace fill against available return capacity.",
        "Large reliable fleet partners": "Prefer for anchor corridors, SLA-heavy work, and repeat route assignment.",
        "Claims-sensitive operators": "Use only when cargo is lower value or when additional checks are applied.",
        "Cancellation-risk capacity": "Keep as backup capacity and avoid for urgent cargo.",
        "Specialist flexible operators": "Use for niche routes, staging, and non-standard cargo profiles.",
        "High-frequency domestic passenger flows": "Optimise for fast-moving food, essentials, and high replenishment retail.",
        "Premium long-haul retail flows": "Allocate premium gifting and higher-margin categories near departure flows.",
        "High-uplift destination retail clusters": "Increase inventory depth where route profile shows high sales uplift.",
        "Destination-aware passenger cohorts": "Tune assortments to route culture, compliance, and passenger purpose.",
    }
    return insights.get(label, f"Use this {domain} cluster to tune scoring, capacity allocation, and recommendations.")


def centroid_for(rows: list[VectorRow], features: list[str]) -> dict[str, float]:
    return {
        feature: round(mean([as_float(row["features"].get(feature)) for row in rows]), 2)
        for feature in features
    }


def summarise_clusters(
    domain: str,
    rows: list[VectorRow],
    features: list[str],
    feature_labels: dict[str, str],
    k: int,
) -> dict[str, Any]:
    assignments = run_kmeans(rows, features, k)
    grouped: dict[int, list[VectorRow]] = defaultdict(list)
    for index, row in enumerate(rows):
        grouped[assignments[index]].append(row)

    clusters = []
    for cluster_number, members in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0])):
        centroid = centroid_for(members, features)
        label = cluster_label(domain, centroid)
        clusters.append(
            {
                "id": f"{domain}-{cluster_number + 1}",
                "label": label,
                "size": len(members),
                "centroid": centroid,
                "insight": cluster_insight(domain, label),
                "members": [
                    {
                        "id": member["id"],
                        "label": member["label"],
                        "detail": member["detail"],
                        "metrics": {
                            key: member["features"].get(key)
                            for key in features[:4]
                        },
                    }
                    for member in members[:5]
                ],
            }
        )

    return {
        "domain": domain,
        "title": {
            "routes": "Route Clusters",
            "customers": "Customer Clusters",
            "shipments": "Shipment Clusters",
            "vehicles": "Vehicle And Operator Clusters",
            "passengers": "Passenger Retail Clusters",
        }[domain],
        "description": {
            "routes": "Groups corridors by distance, empty-kilometre exposure, service reliability, available capacity, and demand density.",
            "customers": "Groups shippers by shipment frequency, total tonnes, urgency, revenue, reliability, and regulated-cargo exposure.",
            "shipments": "Groups individual loads by tonnes, revenue, detour, urgency, cargo fit, driver score, and schedule pressure.",
            "vehicles": "Groups operators by fleet scale, mode mix, on-time history, cancellation rate, and claims risk.",
            "passengers": "Groups airport retail passenger routes by weekly flights, revenue base, compliance profile, assortment mix, and uplift.",
        }[domain],
        "model": "deterministic k-means",
        "features": [{"key": key, "label": feature_labels[key]} for key in features],
        "clusters": clusters,
    }


def flatten_shipments(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {**shipment, "corridorId": corridor["id"], "corridorName": corridor["name"]}
        for corridor in dataset["corridors"]
        for shipment in corridor["shipments"]
    ]


def build_route_rows(dataset: dict[str, Any]) -> list[VectorRow]:
    rows = []
    for corridor in dataset["corridors"]:
        capacity = sum(as_int(mode["capacity"]) for mode in corridor["modes"])
        availability = mean([as_float(mode["available"]) for mode in corridor["modes"]])
        shipment_tonnes = sum(as_int(shipment["tonnes"]) for shipment in corridor["shipments"])
        rows.append(
            {
                "id": corridor["id"],
                "label": corridor["name"],
                "detail": corridor["returnLane"],
                "features": {
                    "distanceKm": as_int(corridor["distanceKm"]),
                    "baselineEmptyKm": as_int(corridor["baselineEmptyKm"]),
                    "baseAnchorTonnes": as_int(corridor["baseAnchorTonnes"]),
                    "vehicles": as_int(corridor["vehicles"]),
                    "serviceLevel": as_int(corridor["serviceLevel"]),
                    "totalCapacityTonnes": capacity,
                    "avgAvailability": round(availability, 2),
                    "shipmentTonnes": shipment_tonnes,
                },
            }
        )
    return rows


def build_customer_rows(dataset: dict[str, Any]) -> list[VectorRow]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for shipment in flatten_shipments(dataset):
        grouped[str(shipment["shipper"])].append(shipment)

    rows = []
    for shipper, shipments in grouped.items():
        total_tonnes = sum(as_int(item["tonnes"]) for item in shipments)
        regulated = [item for item in shipments if item.get("compatibility") == "regulated"]
        rows.append(
            {
                "id": shipper,
                "label": shipper,
                "detail": f"{len(shipments)} shipments across {len({item['corridorId'] for item in shipments})} corridors",
                "features": {
                    "shipmentCount": len(shipments),
                    "totalTonnes": total_tonnes,
                    "avgRevenuePerTon": round(mean([as_float(item["revenuePerTon"]) for item in shipments]), 2),
                    "avgUrgency": round(mean([as_float(item["urgency"]) for item in shipments]), 2),
                    "avgReliability": round(mean([as_float(item["reliability"]) for item in shipments]), 2),
                    "regulatedShare": round((len(regulated) / len(shipments)) * 100, 2),
                    "avgDriverScore": round(mean([as_float(item.get("driverScore"), 78) for item in shipments]), 2),
                },
            }
        )
    return rows


def build_shipment_rows(dataset: dict[str, Any]) -> list[VectorRow]:
    rows = []
    for shipment in flatten_shipments(dataset):
        rows.append(
            {
                "id": shipment["id"],
                "label": f"{shipment['cargo']} - {shipment['shipper']}",
                "detail": f"{shipment['origin']} to {shipment['destination']} via {shipment['mode']}",
                "features": {
                    "tonnes": as_int(shipment["tonnes"]),
                    "revenuePerTon": as_int(shipment["revenuePerTon"]),
                    "detourKm": as_int(shipment["detourKm"]),
                    "reliability": as_int(shipment["reliability"]),
                    "urgency": as_int(shipment["urgency"]),
                    "cargoFit": CARGO_FAMILY_FIT.get(str(shipment.get("cargoFamily", "")), 0.76),
                    "driverScore": as_int(shipment.get("driverScore"), 78),
                    "clearanceMinutes": (
                        as_int(shipment.get("handlingMinutes"))
                        + as_int(shipment.get("securityMinutes"))
                        + as_int(shipment.get("customsMinutes"))
                        + as_int(shipment.get("layoverMinutes"))
                    ),
                },
            }
        )
    return rows


def build_vehicle_rows(dataset: dict[str, Any]) -> list[VectorRow]:
    rows = []
    for partner in dataset["partners"]:
        modes = partner["modes"]
        rows.append(
            {
                "id": partner["id"],
                "label": partner["name"],
                "detail": f"{partner['type']} in {partner['homeRegion']}",
                "features": {
                    "fleetSize": as_int(partner["fleetSize"]),
                    "onTimePercent": as_int(partner["onTimePercent"]),
                    "cancellationRatePercent": as_float(partner["cancellationRatePercent"]),
                    "claimsRatePercent": as_float(partner["claimsRatePercent"]),
                    "modeCount": len(modes),
                    "airEnabled": 1 if "air" in modes else 0,
                    "seaEnabled": 1 if "sea" in modes else 0,
                    "stagingEnabled": 1 if "staging" in modes else 0,
                },
            }
        )
    return rows


def build_passenger_rows(dataset: dict[str, Any]) -> list[VectorRow]:
    rows = []
    for profile in dataset["retailProfiles"]:
        assortments = profile["assortments"]
        weighted_uplift = sum(as_float(item["share"]) * as_float(item["uplift"]) for item in assortments) / 100
        premium_share = sum(
            as_float(item["share"])
            for item in assortments
            if any(keyword in str(item["label"]).lower() for keyword in ["premium", "luxury", "designer"])
        )
        essentials_share = sum(
            as_float(item["share"])
            for item in assortments
            if any(keyword in str(item["label"]).lower() for keyword in ["essentials", "health", "snacks"])
        )
        rows.append(
            {
                "id": profile["id"],
                "label": profile["name"],
                "detail": profile["passengerMix"],
                "features": {
                    "weeklyFlights": as_int(profile["weeklyFlights"]),
                    "baseRevenue": as_int(profile["baseRevenue"]),
                    "weightedUplift": round(weighted_uplift, 2),
                    "assortmentCount": len(assortments),
                    "premiumShare": premium_share,
                    "essentialsShare": essentials_share,
                },
            }
        )
    return rows


def build_clusters(dataset: dict[str, Any]) -> dict[str, Any]:
    route_features = [
        "distanceKm",
        "baselineEmptyKm",
        "baseAnchorTonnes",
        "vehicles",
        "serviceLevel",
        "totalCapacityTonnes",
        "avgAvailability",
        "shipmentTonnes",
    ]
    customer_features = [
        "shipmentCount",
        "totalTonnes",
        "avgRevenuePerTon",
        "avgUrgency",
        "avgReliability",
        "regulatedShare",
        "avgDriverScore",
    ]
    shipment_features = [
        "tonnes",
        "revenuePerTon",
        "detourKm",
        "reliability",
        "urgency",
        "cargoFit",
        "driverScore",
        "clearanceMinutes",
    ]
    vehicle_features = [
        "fleetSize",
        "onTimePercent",
        "cancellationRatePercent",
        "claimsRatePercent",
        "modeCount",
        "airEnabled",
        "seaEnabled",
        "stagingEnabled",
    ]
    passenger_features = [
        "weeklyFlights",
        "baseRevenue",
        "weightedUplift",
        "assortmentCount",
        "premiumShare",
        "essentialsShare",
    ]

    feature_labels = {
        "distanceKm": "Distance km",
        "baselineEmptyKm": "Baseline empty km",
        "baseAnchorTonnes": "Anchor tonnes",
        "vehicles": "Vehicles",
        "serviceLevel": "Service level",
        "totalCapacityTonnes": "Capacity tonnes",
        "avgAvailability": "Average availability",
        "shipmentTonnes": "Shipment tonnes",
        "shipmentCount": "Shipment count",
        "totalTonnes": "Total tonnes",
        "avgRevenuePerTon": "Average revenue per tonne",
        "avgUrgency": "Average urgency",
        "avgReliability": "Average reliability",
        "regulatedShare": "Regulated share",
        "avgDriverScore": "Average driver score",
        "tonnes": "Tonnes",
        "revenuePerTon": "Revenue per tonne",
        "detourKm": "Detour km",
        "reliability": "Reliability",
        "urgency": "Urgency",
        "cargoFit": "Cargo fit",
        "driverScore": "Driver score",
        "clearanceMinutes": "Clearance minutes",
        "fleetSize": "Fleet size",
        "onTimePercent": "On-time percent",
        "cancellationRatePercent": "Cancellation rate",
        "claimsRatePercent": "Claims rate",
        "modeCount": "Mode count",
        "airEnabled": "Air enabled",
        "seaEnabled": "Sea enabled",
        "stagingEnabled": "Staging enabled",
        "weeklyFlights": "Weekly flights",
        "baseRevenue": "Base revenue",
        "weightedUplift": "Weighted uplift",
        "assortmentCount": "Assortment count",
        "premiumShare": "Premium share",
        "essentialsShare": "Essentials share",
    }

    domains = [
        summarise_clusters("routes", build_route_rows(dataset), route_features, feature_labels, 4),
        summarise_clusters("customers", build_customer_rows(dataset), customer_features, feature_labels, 5),
        summarise_clusters("shipments", build_shipment_rows(dataset), shipment_features, feature_labels, 5),
        summarise_clusters("vehicles", build_vehicle_rows(dataset), vehicle_features, feature_labels, 4),
        summarise_clusters("passengers", build_passenger_rows(dataset), passenger_features, feature_labels, 3),
    ]

    return {
        "model": "K-means clustering",
        "refreshPolicy": "Recomputed from the local CSV-backed dataset whenever the backend starts or the endpoint is called.",
        "domains": domains,
    }
