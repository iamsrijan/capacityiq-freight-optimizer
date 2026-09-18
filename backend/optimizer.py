from __future__ import annotations

from typing import Any

from config import COMPATIBILITY_FIT, MODE_TARGET_FILL
from utils import as_int


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

    if mode == "air":
        return (
            f"Book {tonnes} t of {cargo} into the next belly-cargo window and keep road movement "
            "limited to first and last mile transfers."
        )
    if mode == "sea":
        return (
            f"Batch {tonnes} t of {cargo} through the feeder or port linkage and use the corridor "
            "only for drayage and consolidation."
        )
    if mode == "staging":
        return (
            f"Stage {tonnes} t of {cargo} at the consolidation buffer, then release it with the "
            "next compatible dispatch wave."
        )
    return (
        f"Assign {tonnes} t of {cargo} to return truck capacity on {corridor['returnLane']} with "
        f"a detour cap of {max_detour} km."
    )


def build_recommended_actions(
    corridor: dict[str, Any],
    accepted: list[dict[str, Any]],
    available_by_mode: dict[str, int],
    max_detour: int,
    guardrail: int,
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
                    f"Score {shipment['score']} from route fit, reliability, revenue and urgency",
                    f"{shipment['detourKm']} km detour is within the {max_detour} km policy",
                    f"{shipment['compatibility']} cargo clears the {guardrail}% compatibility guardrail",
                    f"{shipment['window']} service window with {shipment['reliability']}% reliability",
                ],
                "revenue": revenue,
                "emptyKmAvoided": empty_km,
                "capacityShare": capacity_share,
                "timing": f"Pickup {shipment.get('pickupWindow', shipment['window'])}; deliver by {shipment.get('deliveryWindow', shipment['window'])}",
            }
        )

    return actions


def score_shipment(shipment: dict[str, Any], max_detour: int, guardrail: int) -> int:
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
        mode_remaining = remaining_bookable.get(mode, 0)
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
        ),
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
