from __future__ import annotations

from typing import Any

from config import CARGO_FAMILY_FIT, COMPATIBILITY_FIT, CONTRACT_FIT, MODE_TARGET_FILL
from utils import as_int


def clamp_percent(value: float) -> float:
    return max(0, min(1, value))


def clearance_minutes(shipment: dict[str, Any]) -> int:
    return (
        as_int(shipment.get("handlingMinutes"))
        + as_int(shipment.get("securityMinutes"))
        + as_int(shipment.get("customsMinutes"))
        + as_int(shipment.get("layoverMinutes"))
    )


def cargo_family_fit(shipment: dict[str, Any]) -> float:
    return CARGO_FAMILY_FIT.get(str(shipment.get("cargoFamily", "")), 0.76)


def contract_fit(shipment: dict[str, Any]) -> float:
    return CONTRACT_FIT.get(str(shipment.get("contractType", "spot market")), 0.68)


def schedule_fit(shipment: dict[str, Any], max_clearance_minutes: int) -> float:
    if shipment.get("mode") != "air" and shipment.get("compatibility") != "regulated":
        return 1

    clearance = clearance_minutes(shipment)
    if max_clearance_minutes <= 0:
        return 0

    soft_target = max_clearance_minutes * 0.5
    overage = max(0, clearance - soft_target)
    return clamp_percent(1 - overage / max(max_clearance_minutes, 1))


def shipment_risk_flags(
    shipment: dict[str, Any],
    min_driver_score: int,
    max_clearance_minutes: int,
    prefer_contracted: bool,
) -> list[str]:
    flags = []
    driver_score = as_int(shipment.get("driverScore"), 78)
    route_trips = as_int(shipment.get("routeFamiliarityTrips"))
    clearance = clearance_minutes(shipment)
    family_fit = cargo_family_fit(shipment)
    contract_type = str(shipment.get("contractType", "spot market"))

    if driver_score < min_driver_score:
        flags.append("Driver score below scenario floor")
    if route_trips < 8:
        flags.append("Low route familiarity")
    if family_fit < 0.68:
        flags.append("Strict cargo segregation needed")
    if shipment.get("mode") == "air" and clearance > max_clearance_minutes:
        flags.append("Airport clearance exceeds scenario cap")
    if prefer_contracted and contract_type == "spot market":
        flags.append("Spot-market capacity")

    return flags


def route_anchor_node(label: str) -> str:
    primary = label.split("+", 1)[0].split("/", 1)[0].strip()
    return primary or label


def route_anchor_nodes(label: str) -> list[str]:
    nodes = []
    for part in label.replace("+", "/").split("/"):
        node = part.strip()
        if node and node not in nodes:
            nodes.append(node)
    return nodes or [label]


def route_nodes_for(corridor: dict[str, Any], shipment: dict[str, Any]) -> list[str]:
    corridor_origin = route_anchor_node(str(corridor["origin"]))
    corridor_origin_nodes = route_anchor_nodes(str(corridor["origin"]))
    corridor_destination = route_anchor_node(str(corridor["destination"]))
    corridor_destination_nodes = route_anchor_nodes(str(corridor["destination"]))
    mode = str(shipment["mode"])

    if mode == "air":
        nodes = [
            shipment["origin"],
            f"{corridor_destination} air cargo window",
            f"{corridor_origin} air gateway",
            shipment["destination"],
        ]
    elif mode == "sea":
        nodes = [
            shipment["origin"],
            f"{corridor_destination} feeder consolidation",
            f"{corridor_origin} port linkage",
            shipment["destination"],
        ]
    elif mode == "staging":
        nodes = [
            shipment["origin"],
            f"{corridor_destination} staging area",
            f"{corridor_origin} consolidation hub",
            shipment["destination"],
        ]
    else:
        nodes = [
            shipment["origin"],
            *corridor_destination_nodes,
            *reversed(corridor_origin_nodes),
            shipment["destination"],
        ]

    deduped: list[str] = []
    for node in nodes:
        node_text = str(node).strip()
        if node_text and node_text not in deduped:
            deduped.append(node_text)
    return deduped


def instruction_for(corridor: dict[str, Any], shipment: dict[str, Any], max_detour: int) -> str:
    mode = str(shipment["mode"])
    tonnes = as_int(shipment["matchedTonnes"])
    cargo = str(shipment["cargo"]).lower()
    vehicle = shipment.get("vehicleProfile") or "compatible vehicle"
    driver_score = as_int(shipment.get("driverScore"), 78)
    route_trips = as_int(shipment.get("routeFamiliarityTrips"))

    if mode == "air":
        return (
            f"Book {tonnes} t of {cargo} into {vehicle.lower()} with a {driver_score} driver score "
            "and keep road movement limited to first and last mile transfers."
        )
    if mode == "sea":
        return (
            f"Batch {tonnes} t of {cargo} through {vehicle.lower()} and use the corridor only for "
            "drayage and consolidation."
        )
    if mode == "staging":
        return (
            f"Stage {tonnes} t of {cargo} in {vehicle.lower()}, then release it with the next "
            "compatible dispatch wave."
        )
    return (
        f"Assign {tonnes} t of {cargo} to {vehicle.lower()} on {corridor['returnLane']} with "
        f"a detour cap of {max_detour} km and {route_trips} prior route trips."
    )


def schedule_plan_for(shipment: dict[str, Any], max_clearance_minutes: int) -> str:
    clearance = clearance_minutes(shipment)
    peak_window = shipment.get("peakWindow") or "next dispatch wave"

    if shipment.get("mode") == "air":
        airport_pair = shipment.get("airportPair") or "nearest cargo gateway"
        return (
            f"{airport_pair}; peak window {peak_window}; {clearance} min handling/security/customs "
            f"against {max_clearance_minutes} min cap."
        )

    return (
        f"Dispatch in {peak_window}; historical transit {shipment.get('avgTransitHours', 0)} h; "
        f"{clearance} min handling buffer."
    )


def build_recommended_actions(
    corridor: dict[str, Any],
    accepted: list[dict[str, Any]],
    available_by_mode: dict[str, int],
    max_detour: int,
    guardrail: int,
    max_clearance_minutes: int,
) -> list[dict[str, Any]]:
    actions = []
    for index, shipment in enumerate(accepted[:6], start=1):
        matched_tonnes = as_int(shipment["matchedTonnes"])
        mode = str(shipment["mode"])
        revenue = matched_tonnes * as_int(shipment["revenuePerTon"])
        empty_km = round(
            (matched_tonnes / (16 if mode == "road" else 24))
            * max(120, as_int(corridor["distanceKm"]) - as_int(shipment["detourKm"]))
        )
        available = max(available_by_mode.get(mode, 0), 1)
        capacity_share = round((matched_tonnes / available) * 100)
        route = route_nodes_for(corridor, shipment)

        actions.append(
            {
                "id": f"ACT-{index:02d}-{shipment['id']}",
                "shipmentId": shipment["id"],
                "headline": f"Move {matched_tonnes} t of {shipment['cargo']} by {mode}",
                "shipper": shipment["shipper"],
                "cargo": shipment["cargo"],
                "mode": mode,
                "matchedTonnes": matched_tonnes,
                "route": route,
                "routeText": " -> ".join(route),
                "operatingInstruction": instruction_for(corridor, shipment, max_detour),
                "why": [
                    f"Score {shipment['score']} from route fit, reliability, revenue, cargo fit, operating quality and K-means cluster fit",
                    f"K-means group: {shipment.get('clusterLabel', 'standard shipment cluster')} with {round(float(shipment.get('clusterFit', 0)) * 100)}% cluster fit",
                    f"{shipment['detourKm']} km detour is within the {max_detour} km policy",
                    f"{shipment['compatibility']} cargo clears the {guardrail}% compatibility guardrail",
                    f"{shipment.get('contractType', 'spot market')} with driver score {shipment.get('driverScore', 78)} and {shipment.get('routeFamiliarityTrips', 0)} prior route trips",
                    f"{shipment.get('window')} service window with {shipment['reliability']}% reliability",
                ],
                "revenue": revenue,
                "emptyKmAvoided": empty_km,
                "capacityShare": capacity_share,
                "timing": f"Pickup {shipment.get('pickupWindow', shipment['window'])}; deliver by {shipment.get('deliveryWindow', shipment['window'])}",
                "assignedVehicle": shipment.get("vehicleProfile"),
                "driverScore": as_int(shipment.get("driverScore"), 78),
                "routeFamiliarityTrips": as_int(shipment.get("routeFamiliarityTrips")),
                "contractType": shipment.get("contractType"),
                "averageTransitHours": shipment.get("avgTransitHours"),
                "averageMonthlyCost": as_int(shipment.get("avgMonthlyCost")),
                "compatibilityNote": shipment.get("compatibilityNote"),
                "schedulePlan": schedule_plan_for(shipment, max_clearance_minutes),
                "riskFlags": shipment.get("riskFlags", []),
                "clusterLabel": shipment.get("clusterLabel"),
                "clusterFit": shipment.get("clusterFit"),
                "clusterAdjustment": shipment.get("clusterAdjustment"),
                "clusterInsight": shipment.get("clusterInsight"),
            }
        )

    return actions


def score_shipment(
    shipment: dict[str, Any],
    max_detour: int,
    guardrail: int,
    min_driver_score: int,
    max_clearance_minutes: int,
    prefer_contracted: bool,
    cluster_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    route_fit = max(0, 1 - as_int(shipment["detourKm"]) / max(max_detour, 1))
    reliability_fit = as_int(shipment["reliability"]) / 100
    revenue_fit = min(as_int(shipment["revenuePerTon"]) / 12000, 1)
    urgency_fit = as_int(shipment["urgency"]) / 100
    compatibility_fit = COMPATIBILITY_FIT.get(str(shipment["compatibility"]), 0.5)
    family_fit = cargo_family_fit(shipment)
    driver_fit = as_int(shipment.get("driverScore"), 78) / 100
    route_familiarity_fit = min(as_int(shipment.get("routeFamiliarityTrips")) / 50, 1)
    contract_strength = contract_fit(shipment)
    timing_fit = schedule_fit(shipment, max_clearance_minutes)
    cluster_fit = float(cluster_profile.get("fit", 0.72)) if cluster_profile else 0.72
    cluster_adjustment = int(cluster_profile.get("adjustment", 0)) if cluster_profile else 0
    guardrail_penalty = ((guardrail - 50) / 50) * (1 - compatibility_fit) * 22
    driver_penalty = max(0, min_driver_score - as_int(shipment.get("driverScore"), 78)) * 0.35
    contract_penalty = 5 if prefer_contracted and shipment.get("contractType") == "spot market" else 0
    clearance_penalty = max(0, clearance_minutes(shipment) - max_clearance_minutes) / 60 * 4

    score = round(
        route_fit * 22
        + reliability_fit * 17
        + compatibility_fit * 13
        + family_fit * 12
        + revenue_fit * 10
        + urgency_fit * 6
        + driver_fit * 8
        + route_familiarity_fit * 6
        + contract_strength * 4
        + timing_fit * 2
        + cluster_adjustment
        - guardrail_penalty
        - driver_penalty
        - contract_penalty
        - clearance_penalty
    )

    return {
        "score": max(0, min(100, score)),
        "scoring": {
            "routeFit": round(route_fit, 2),
            "reliabilityFit": round(reliability_fit, 2),
            "compatibilityFit": round(compatibility_fit, 2),
            "cargoFit": round(family_fit, 2),
            "driverFit": round(driver_fit, 2),
            "routeFamiliarityFit": round(route_familiarity_fit, 2),
            "contractFit": round(contract_strength, 2),
            "scheduleFit": round(timing_fit, 2),
            "clusterFit": round(cluster_fit, 2),
            "clusterAdjustment": cluster_adjustment,
        },
        "clusterLabel": cluster_profile.get("label") if cluster_profile else "Scenario baseline cluster",
        "clusterFit": round(cluster_fit, 2),
        "clusterAdjustment": cluster_adjustment,
        "clusterInsight": cluster_profile.get("insight") if cluster_profile else "No K-means segment was available for this shipment.",
        "riskFlags": shipment_risk_flags(
            shipment,
            min_driver_score,
            max_clearance_minutes,
            prefer_contracted,
        ),
    }


def build_operational_summary(
    accepted: list[dict[str, Any]],
    declined: list[dict[str, Any]],
    max_clearance_minutes: int,
) -> dict[str, Any]:
    accepted_count = max(len(accepted), 1)
    contracted = [
        item
        for item in accepted
        if item.get("contractType") and item.get("contractType") != "spot market"
    ]
    compatibility_cleared = [
        item
        for item in accepted
        if "Strict cargo segregation needed" not in item.get("riskFlags", [])
    ]

    return {
        "avgDriverScore": round(sum(as_int(item.get("driverScore"), 78) for item in accepted) / accepted_count),
        "avgRouteFamiliarityTrips": round(
            sum(as_int(item.get("routeFamiliarityTrips")) for item in accepted) / accepted_count
        ),
        "contractedShare": round((len(contracted) / accepted_count) * 100),
        "compatibilityCleared": round((len(compatibility_cleared) / accepted_count) * 100),
        "airClearanceBreaches": sum(
            1
            for item in declined
            if item.get("mode") == "air" and clearance_minutes(item) > max_clearance_minutes
        ),
        "strictCompatibilityRejected": sum(
            1
            for item in declined
            if item.get("reason") in {"Cargo segregation risk too high", "Guardrail confidence too low"}
        ),
        "avgMonthlyCost": round(sum(as_int(item.get("avgMonthlyCost")) for item in accepted) / accepted_count),
        "avgClusterFit": round(
            sum(float(item.get("clusterFit", 0.72)) for item in accepted) / accepted_count * 100
        ),
        "clusterBoostedMatches": sum(1 for item in accepted if as_int(item.get("clusterAdjustment")) > 0),
    }


def optimise_corridor(
    corridor: dict[str, Any],
    anchor_enabled: bool,
    anchor_multiplier: float,
    max_detour: int,
    guardrail: int,
    min_driver_score: int = 72,
    max_clearance_minutes: int = 360,
    prefer_contracted: bool = True,
    cluster_lookup: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    anchor_factor = anchor_multiplier if anchor_enabled else 0.54
    available_by_mode: dict[str, int] = {}
    remaining_bookable: dict[str, int] = {}

    for item in corridor["modes"]:
        available_capacity = round(as_int(item["capacity"]) * (as_int(item["available"]) / 100) * anchor_factor)
        target_fill = MODE_TARGET_FILL.get(str(item["mode"]), 0.86)
        # Bookable capacity is deliberately below available capacity to keep a real-world operating buffer.
        bookable_capacity = round(available_capacity * target_fill) if available_capacity else 0
        available_by_mode[item["mode"]] = available_capacity
        remaining_bookable[item["mode"]] = bookable_capacity

    scored = []
    for shipment in corridor["shipments"]:
        cluster_profile = (cluster_lookup or {}).get(str(shipment["id"]))
        scoring = score_shipment(
            shipment,
            max_detour,
            guardrail,
            min_driver_score,
            max_clearance_minutes,
            prefer_contracted,
            cluster_profile,
        )
        scored.append(
            {
                **shipment,
                "score": scoring["score"],
                "scoring": scoring["scoring"],
                "riskFlags": scoring["riskFlags"],
                "clusterLabel": scoring["clusterLabel"],
                "clusterFit": scoring["clusterFit"],
                "clusterAdjustment": scoring["clusterAdjustment"],
                "clusterInsight": scoring["clusterInsight"],
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
        mode_remaining = remaining_bookable.get(mode, 0)
        incompatible = guardrail >= 82 and shipment["compatibility"] in {"chilled", "regulated"}
        cargo_blocked = guardrail >= 82 and cargo_family_fit(shipment) < 0.68
        detour_blocked = shipment["mode"] != "air" and as_int(shipment["detourKm"]) > max_detour
        driver_blocked = as_int(shipment.get("driverScore"), 78) < min_driver_score
        clearance_blocked = (
            shipment["mode"] == "air" and clearance_minutes(shipment) > max_clearance_minutes
        )

        if mode_remaining <= 0:
            declined.append({**shipment, "reason": "No capacity left in this mode"})
            continue

        if detour_blocked:
            declined.append({**shipment, "reason": "Detour exceeds lane policy"})
            continue

        if driver_blocked:
            declined.append({**shipment, "reason": "Driver score below scenario floor"})
            continue

        if clearance_blocked:
            declined.append({**shipment, "reason": "Airport clearance window too tight"})
            continue

        if cargo_blocked:
            declined.append({**shipment, "reason": "Cargo segregation risk too high"})
            continue

        if shipment["score"] < threshold or incompatible:
            declined.append({**shipment, "reason": "Guardrail confidence too low"})
            continue

        matched_tonnes = min(as_int(shipment["tonnes"]), mode_remaining)
        remaining_bookable[mode] = mode_remaining - matched_tonnes
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
    total_remaining: dict[str, int] = {}
    for item in corridor["modes"]:
        mode = str(item["mode"])
        available = available_by_mode[mode]
        target_fill = MODE_TARGET_FILL.get(mode, 0.86)
        bookable_capacity = round(available * target_fill) if available else 0
        bookable_remaining = remaining_bookable.get(mode, 0)
        used = max(0, bookable_capacity - bookable_remaining)
        mode_remaining = max(0, available - used)
        total_remaining[mode] = mode_remaining
        utilisation = round((used / available) * 100) if available else 0
        mode_utilisation.append(
            {
                **item,
                "availableTonnes": available,
                "bookableTonnes": bookable_capacity,
                "remainingTonnes": mode_remaining,
                "reserveTonnes": max(0, available - bookable_capacity),
                "usedTonnes": used,
                "utilisation": utilisation,
            }
        )

    return {
        "accepted": accepted,
        "declined": declined,
        "recommendedActions": build_recommended_actions(
            corridor,
            accepted,
            available_by_mode,
            max_detour,
            guardrail,
            max_clearance_minutes,
        ),
        "operationalSummary": build_operational_summary(accepted, declined, max_clearance_minutes),
        "remaining": total_remaining,
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
