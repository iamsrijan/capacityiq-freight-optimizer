from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "backend" / "data"
SEED = 20260915


CORRIDORS = [
    {
        "id": "northeast",
        "name": "Northeast Backhaul",
        "anchor": "Britannia Kolkata to Guwahati loop",
        "origin": "Kolkata / Siliguri",
        "destination": "Guwahati + Upper Assam",
        "return_lane": "Northeast to East and North India",
        "recurring": "6 dispatch waves per week",
        "distance_km": 1120,
        "baseline_empty_km": 87000,
        "base_anchor_tonnes": 2420,
        "vehicles": 176,
        "service_level": 91,
        "region": "East and Northeast",
        "origins": ["Guwahati", "Dibrugarh", "Jorhat", "Shillong", "Aizawl", "Agartala", "Silchar"],
        "destinations": ["Kolkata", "Haldia port", "Delhi NCR", "Patna", "Lucknow", "Bengaluru"],
    },
    {
        "id": "west",
        "name": "Western FMCG Loop",
        "anchor": "Britannia Pune to Rajasthan distribution",
        "origin": "Pune / Nashik",
        "destination": "Jaipur + Jodhpur",
        "return_lane": "Rajasthan to Maharashtra and South",
        "recurring": "4 dispatch waves per week",
        "distance_km": 940,
        "baseline_empty_km": 52000,
        "base_anchor_tonnes": 1680,
        "vehicles": 118,
        "service_level": 88,
        "region": "West",
        "origins": ["Jaipur", "Jodhpur", "Kishangarh", "Bhilwara", "Udaipur", "Bikaner"],
        "destinations": ["Pune", "Mumbai", "Nashik", "Bengaluru", "Chennai", "Nhava Sheva"],
    },
    {
        "id": "coastal",
        "name": "Coastal Export Relay",
        "anchor": "Britannia Chennai to Kerala replenishment",
        "origin": "Chennai",
        "destination": "Kochi + Calicut",
        "return_lane": "Kerala to Tamil Nadu and export ports",
        "recurring": "5 dispatch waves per week",
        "distance_km": 720,
        "baseline_empty_km": 43000,
        "base_anchor_tonnes": 1320,
        "vehicles": 94,
        "service_level": 93,
        "region": "South Coast",
        "origins": ["Kochi", "Calicut", "Alappuzha", "Kannur", "Kottayam", "Coimbatore"],
        "destinations": ["Chennai", "Bengaluru", "Hyderabad", "Tuticorin port", "Mangaluru", "Mumbai"],
    },
    {
        "id": "north",
        "name": "North Market Rebalance",
        "anchor": "Britannia Delhi NCR to Punjab and Himachal",
        "origin": "Delhi NCR",
        "destination": "Ludhiana + Baddi",
        "return_lane": "Punjab and Himachal to NCR",
        "recurring": "7 dispatch waves per week",
        "distance_km": 520,
        "baseline_empty_km": 41000,
        "base_anchor_tonnes": 1880,
        "vehicles": 132,
        "service_level": 90,
        "region": "North",
        "origins": ["Ludhiana", "Baddi", "Amritsar", "Jalandhar", "Chandigarh", "Una"],
        "destinations": ["Delhi NCR", "Jaipur", "Lucknow", "Kanpur", "Indore", "Gurugram"],
    },
    {
        "id": "east-port",
        "name": "East Port Connector",
        "anchor": "Britannia Bhubaneswar to Odisha and Bengal",
        "origin": "Bhubaneswar / Cuttack",
        "destination": "Kolkata + Paradip",
        "return_lane": "Odisha ports to eastern consumption hubs",
        "recurring": "5 dispatch waves per week",
        "distance_km": 480,
        "baseline_empty_km": 36000,
        "base_anchor_tonnes": 1160,
        "vehicles": 86,
        "service_level": 89,
        "region": "East Coast",
        "origins": ["Paradip", "Cuttack", "Rourkela", "Balasore", "Jharsuguda", "Angul"],
        "destinations": ["Kolkata", "Bhubaneswar", "Ranchi", "Jamshedpur", "Raipur", "Patna"],
    },
    {
        "id": "bengaluru-export",
        "name": "Bengaluru Export Feeder",
        "anchor": "Britannia Bengaluru to Mangaluru and Goa",
        "origin": "Bengaluru",
        "destination": "Mangaluru + Goa",
        "return_lane": "Coastal Karnataka to Bengaluru and export gateways",
        "recurring": "6 dispatch waves per week",
        "distance_km": 640,
        "baseline_empty_km": 39000,
        "base_anchor_tonnes": 1420,
        "vehicles": 102,
        "service_level": 92,
        "region": "Southwest",
        "origins": ["Mangaluru", "Goa", "Udupi", "Hassan", "Mysuru", "Hubballi"],
        "destinations": ["Bengaluru", "Chennai", "Hyderabad", "Mumbai", "Cochin port", "Tuticorin port"],
    },
    {
        "id": "delhi-ncr",
        "name": "Delhi NCR Urban Ring",
        "anchor": "Britannia NCR urban replenishment",
        "origin": "Greater Noida / Sonipat",
        "destination": "Delhi NCR retail ring",
        "return_lane": "NCR spokes to consolidation hubs",
        "recurring": "14 dispatch waves per week",
        "distance_km": 210,
        "baseline_empty_km": 28000,
        "base_anchor_tonnes": 980,
        "vehicles": 148,
        "service_level": 94,
        "region": "Metro North",
        "origins": ["Noida", "Gurugram", "Sonipat", "Faridabad", "Ghaziabad", "Manesar"],
        "destinations": ["Greater Noida", "Kundli", "Delhi", "Panipat", "Meerut", "Jaipur"],
    },
    {
        "id": "central",
        "name": "Central India Crossdock",
        "anchor": "Britannia Nagpur to MP and Chhattisgarh",
        "origin": "Nagpur",
        "destination": "Indore + Raipur",
        "return_lane": "Central India to national hubs",
        "recurring": "5 dispatch waves per week",
        "distance_km": 690,
        "baseline_empty_km": 44000,
        "base_anchor_tonnes": 1380,
        "vehicles": 108,
        "service_level": 87,
        "region": "Central",
        "origins": ["Indore", "Raipur", "Bhopal", "Jabalpur", "Bilaspur", "Akola"],
        "destinations": ["Nagpur", "Pune", "Hyderabad", "Kolkata", "Ahmedabad", "Delhi NCR"],
    },
    {
        "id": "kashmir",
        "name": "Kashmir Seasonal Return",
        "anchor": "Britannia Jammu to Srinagar seasonal loop",
        "origin": "Jammu",
        "destination": "Srinagar + Baramulla",
        "return_lane": "Kashmir valley to north Indian markets",
        "recurring": "3 dispatch waves per week",
        "distance_km": 310,
        "baseline_empty_km": 24000,
        "base_anchor_tonnes": 760,
        "vehicles": 64,
        "service_level": 84,
        "region": "North Hills",
        "origins": ["Srinagar", "Baramulla", "Pulwama", "Anantnag", "Sopore", "Jammu"],
        "destinations": ["Jammu", "Delhi NCR", "Amritsar", "Chandigarh", "Ludhiana", "Jaipur"],
    },
    {
        "id": "hyderabad",
        "name": "Hyderabad Pharma Backhaul",
        "anchor": "Britannia Hyderabad to Telangana and AP",
        "origin": "Hyderabad",
        "destination": "Vijayawada + Visakhapatnam",
        "return_lane": "Andhra and Telangana to pharma and port hubs",
        "recurring": "6 dispatch waves per week",
        "distance_km": 620,
        "baseline_empty_km": 40000,
        "base_anchor_tonnes": 1510,
        "vehicles": 116,
        "service_level": 93,
        "region": "Telugu States",
        "origins": ["Visakhapatnam", "Vijayawada", "Warangal", "Kurnool", "Guntur", "Nellore"],
        "destinations": ["Hyderabad", "Bengaluru", "Chennai", "Mumbai", "Nagpur", "Pune"],
    },
    {
        "id": "gujarat",
        "name": "Gujarat Export Loop",
        "anchor": "Britannia Ahmedabad to Kutch and Saurashtra",
        "origin": "Ahmedabad",
        "destination": "Rajkot + Kandla",
        "return_lane": "Kutch and Saurashtra to west and north markets",
        "recurring": "6 dispatch waves per week",
        "distance_km": 650,
        "baseline_empty_km": 47000,
        "base_anchor_tonnes": 1590,
        "vehicles": 123,
        "service_level": 90,
        "region": "Gujarat",
        "origins": ["Kandla", "Rajkot", "Mundra", "Jamnagar", "Bhuj", "Surat"],
        "destinations": ["Ahmedabad", "Mumbai", "Pune", "Delhi NCR", "Indore", "Jaipur"],
    },
    {
        "id": "eastern-rail",
        "name": "Eastern Rail-Air Relay",
        "anchor": "Britannia Patna to Bengal and Jharkhand",
        "origin": "Patna",
        "destination": "Ranchi + Kolkata",
        "return_lane": "Bihar and Jharkhand to east and north hubs",
        "recurring": "5 dispatch waves per week",
        "distance_km": 580,
        "baseline_empty_km": 37000,
        "base_anchor_tonnes": 1210,
        "vehicles": 98,
        "service_level": 86,
        "region": "Eastern Inland",
        "origins": ["Ranchi", "Jamshedpur", "Dhanbad", "Gaya", "Patna", "Muzaffarpur"],
        "destinations": ["Kolkata", "Delhi NCR", "Lucknow", "Bhubaneswar", "Guwahati", "Raipur"],
    },
]


CARGO_TEMPLATES = [
    ("Packaged tea cartons", "road", "dry", 3600, 5400),
    ("Bamboo panels and handicrafts", "staging", "fragile", 4200, 7200),
    ("Reverse logistics parcels", "staging", "ambient", 4800, 6900),
    ("Regulated pharma samples", "air", "regulated", 12000, 31000),
    ("Speciality ginger and citrus", "road", "chilled", 4300, 7600),
    ("Containerised export overflow", "sea", "dry", 2600, 4600),
    ("Textile bales", "road", "dry", 3100, 5100),
    ("Spice cartons", "road", "ambient", 3900, 6200),
    ("Medical devices", "air", "regulated", 14000, 26000),
    ("Premium craft consignments", "staging", "fragile", 5200, 8800),
    ("Electronics returns", "staging", "ambient", 5200, 8300),
    ("Frozen bakery inputs", "road", "chilled", 5600, 9200),
    ("Coffee and cocoa sacks", "sea", "dry", 2800, 4300),
    ("High value samples", "air", "regulated", 21000, 38000),
    ("Durable snacks overflow", "road", "ambient", 3000, 4700),
]


RETAIL_PROFILES = [
    {
        "id": "africa",
        "name": "African Routes",
        "terminal": "International departures pier B",
        "passenger_mix": "Traders, students, VFR, cultural tourism",
        "weekly_flights": 32,
        "base_revenue": 18200000,
        "compliance": "Alcohol secondary, handicraft-led mix",
        "assortments": [
            ("Indian and African handicrafts", 30, 18),
            ("Tea, coffee and sweets gifting", 24, 14),
            ("Durable snacks", 18, 9),
            ("Travel electronics", 15, 7),
            ("Beauty and wellness", 13, 6),
        ],
    },
    {
        "id": "uk",
        "name": "UK Routes",
        "terminal": "Premium duty-paid corridor",
        "passenger_mix": "Business, diaspora, leisure, premium gifting",
        "weekly_flights": 46,
        "base_revenue": 26400000,
        "compliance": "Premium spirits where legally permitted",
        "assortments": [
            ("Premium Indian spirits", 26, 20),
            ("Luxury sweets and bakery gifting", 22, 13),
            ("Tea, coffee and wellness", 20, 11),
            ("Designer craft", 17, 8),
            ("Travel essentials", 15, 5),
        ],
    },
    {
        "id": "saudi",
        "name": "Saudi Routes",
        "terminal": "Family and pilgrimage retail zone",
        "passenger_mix": "Pilgrimage, family travel, workers, gifting",
        "weekly_flights": 58,
        "base_revenue": 23900000,
        "compliance": "Destination-appropriate non-liquor mix",
        "assortments": [
            ("Dates, sweets and bakery gifting", 28, 16),
            ("Fragrance and personal care", 24, 12),
            ("Modest fashion accessories", 18, 8),
            ("Travel health essentials", 17, 7),
            ("Prayer and family travel items", 13, 6),
        ],
    },
    {
        "id": "south-east-asia",
        "name": "South East Asia Routes",
        "terminal": "International transfer retail strip",
        "passenger_mix": "Leisure, business, students, compact gifting",
        "weekly_flights": 64,
        "base_revenue": 25100000,
        "compliance": "Compact gifting and travel essentials",
        "assortments": [
            ("Premium snacks and sweets", 25, 14),
            ("Ayurveda and wellness", 20, 11),
            ("Beauty minis", 18, 10),
            ("Travel electronics", 17, 7),
            ("Tea and coffee gifting", 20, 9),
        ],
    },
    {
        "id": "middle-east",
        "name": "Middle East Business Routes",
        "terminal": "Business-heavy international concourse",
        "passenger_mix": "Workers, business, family, gifting",
        "weekly_flights": 72,
        "base_revenue": 27800000,
        "compliance": "Destination aware gifting and essentials",
        "assortments": [
            ("Fragrance and personal care", 24, 13),
            ("Sweets and bakery gifting", 23, 12),
            ("Travel health", 17, 8),
            ("Premium dates and nuts", 20, 10),
            ("Family travel essentials", 16, 6),
        ],
    },
    {
        "id": "domestic-metro",
        "name": "Domestic Metro Routes",
        "terminal": "High-frequency domestic pier",
        "passenger_mix": "Business, weekend leisure, quick purchases",
        "weekly_flights": 188,
        "base_revenue": 31500000,
        "compliance": "Fast checkout, high replenishment categories",
        "assortments": [
            ("Ready-to-eat snacks", 26, 12),
            ("Coffee and bakery", 22, 10),
            ("Travel essentials", 20, 7),
            ("Impulse sweets", 16, 8),
            ("Personal care minis", 16, 5),
        ],
    },
    {
        "id": "europe",
        "name": "Europe Long Haul Routes",
        "terminal": "Premium long-haul departure wing",
        "passenger_mix": "Leisure, business, diaspora, premium gifting",
        "weekly_flights": 38,
        "base_revenue": 28600000,
        "compliance": "Premium gifting with destination rules",
        "assortments": [
            ("Premium Indian spirits", 22, 17),
            ("Designer craft and textiles", 20, 11),
            ("Luxury sweets", 21, 12),
            ("Tea, coffee and wellness", 20, 9),
            ("Travel luxury accessories", 17, 7),
        ],
    },
    {
        "id": "north-america",
        "name": "North America Routes",
        "terminal": "Ultra long-haul international zone",
        "passenger_mix": "Diaspora, students, business, long-stay travellers",
        "weekly_flights": 42,
        "base_revenue": 32800000,
        "compliance": "Premium gifting and long-haul essentials",
        "assortments": [
            ("Premium sweets and bakery", 25, 14),
            ("Tea, coffee and wellness", 22, 10),
            ("Designer craft", 17, 8),
            ("Long-haul travel essentials", 18, 7),
            ("Beauty and personal care", 18, 6),
        ],
    },
]


HUB_CITIES = [
    ("Guwahati Consolidation Park", "Guwahati", "Assam"),
    ("Siliguri Gateway Hub", "Siliguri", "West Bengal"),
    ("Haldia Port Buffer", "Haldia", "West Bengal"),
    ("Jaipur Rest And Sort", "Jaipur", "Rajasthan"),
    ("Jodhpur Dry Cargo Yard", "Jodhpur", "Rajasthan"),
    ("Mumbai Air Cargo Annex", "Mumbai", "Maharashtra"),
    ("Pune FMCG Crossdock", "Pune", "Maharashtra"),
    ("Kochi Warehouse Buffer", "Kochi", "Kerala"),
    ("Chennai Export Staging", "Chennai", "Tamil Nadu"),
    ("Bengaluru Airport Cargo", "Bengaluru", "Karnataka"),
    ("Hyderabad Pharma Park", "Hyderabad", "Telangana"),
    ("Nagpur Central Crossdock", "Nagpur", "Maharashtra"),
    ("Indore Reefer Bay", "Indore", "Madhya Pradesh"),
    ("Raipur Inland Terminal", "Raipur", "Chhattisgarh"),
    ("Delhi NCR Urban Node", "Greater Noida", "Uttar Pradesh"),
    ("Sonipat Cold Buffer", "Sonipat", "Haryana"),
    ("Baddi Industrial Staging", "Baddi", "Himachal Pradesh"),
    ("Ludhiana Return Yard", "Ludhiana", "Punjab"),
    ("Jammu Seasonal Hub", "Jammu", "Jammu And Kashmir"),
    ("Srinagar Valley Buffer", "Srinagar", "Jammu And Kashmir"),
    ("Kandla Export Gate", "Kandla", "Gujarat"),
    ("Mundra Container Interface", "Mundra", "Gujarat"),
    ("Ahmedabad Dry Hub", "Ahmedabad", "Gujarat"),
    ("Rajkot Distribution Yard", "Rajkot", "Gujarat"),
    ("Patna Inland Hub", "Patna", "Bihar"),
    ("Ranchi Industrial Crossdock", "Ranchi", "Jharkhand"),
    ("Jamshedpur Metal Cargo Hub", "Jamshedpur", "Jharkhand"),
    ("Paradip Port Yard", "Paradip", "Odisha"),
    ("Bhubaneswar Sortation Hub", "Bhubaneswar", "Odisha"),
    ("Cuttack Food Grade Node", "Cuttack", "Odisha"),
    ("Mangaluru Coastal Yard", "Mangaluru", "Karnataka"),
    ("Goa Light Cargo Hub", "Goa", "Goa"),
    ("Mysuru Staging Centre", "Mysuru", "Karnataka"),
    ("Vijayawada Dry Port", "Vijayawada", "Andhra Pradesh"),
    ("Visakhapatnam Port Connector", "Visakhapatnam", "Andhra Pradesh"),
    ("Warangal Parcel Hub", "Warangal", "Telangana"),
    ("Lucknow North Hub", "Lucknow", "Uttar Pradesh"),
    ("Kanpur Industrial Dock", "Kanpur", "Uttar Pradesh"),
    ("Bhopal Relay Hub", "Bhopal", "Madhya Pradesh"),
    ("Surat Export Sort", "Surat", "Gujarat"),
    ("Coimbatore Textile Hub", "Coimbatore", "Tamil Nadu"),
    ("Tuticorin Port Interface", "Tuticorin", "Tamil Nadu"),
]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def make_capacity_rows(rng: random.Random) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    mode_settings = {
        "road": ("Truck backhaul slots", 1.08, 42, 76),
        "air": ("Belly cargo windows", 0.04, 22, 44),
        "sea": ("Port feeder linkage", 0.24, 25, 56),
        "staging": ("Consolidation buffer", 0.18, 34, 68),
    }
    status_by_mode = {
        "road": "Return-load monetisation opportunity",
        "air": "Premium urgent cargo capacity",
        "sea": "Bulk export and feeder flow",
        "staging": "Cross-dock and rest-area buffer",
    }
    for corridor in CORRIDORS:
        for mode, (label, scale, low, high) in mode_settings.items():
            base = int(corridor["base_anchor_tonnes"])
            capacity = max(28, round(base * scale + rng.randint(-65, 95)))
            rows.append(
                {
                    "corridor_id": corridor["id"],
                    "mode": mode,
                    "label": label,
                    "capacity_tonnes": capacity,
                    "available_percent": rng.randint(low, high),
                    "status": status_by_mode[mode],
                }
            )
    return rows


def make_shipments(rng: random.Random) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    shipper_prefixes = [
        "Eastern",
        "National",
        "Metro",
        "Greenfield",
        "Horizon",
        "Summit",
        "Riverline",
        "PortLink",
        "Healthline",
        "CraftBridge",
        "AgroStar",
        "RetailLoop",
        "Prime",
        "BluePeak",
        "Spice Valley",
        "Tea Garden",
        "Swift",
        "Bharat",
    ]
    shipper_suffixes = [
        "Logistics",
        "Distributors",
        "Export House",
        "Foods",
        "Collective",
        "Industries",
        "Consortium",
        "Forwarders",
        "Supply Co",
        "Trade Network",
    ]
    mode_tonnes = {
        "road": (40, 720),
        "air": (4, 70),
        "sea": (90, 1180),
        "staging": (20, 420),
    }
    start = date(2026, 9, 16)
    shipment_number = 1

    for corridor in CORRIDORS:
        for index in range(200):
            cargo, mode, compatibility, revenue_low, revenue_high = rng.choice(CARGO_TEMPLATES)
            low, high = mode_tonnes[mode]
            tonnes = rng.randint(low, high)
            revenue_per_ton = rng.randrange(revenue_low, revenue_high + 1, 100)
            urgency = rng.randint(24, 99)
            reliability = min(99, max(68, int(rng.gauss(float(corridor["service_level"]), 6))))
            detour_km = int(rng.triangular(8, 245, 74))
            pickup = start + timedelta(days=rng.randint(0, 45))
            delivery = pickup + timedelta(days=rng.randint(1, 6 if mode != "air" else 2))
            window = "12 h" if mode == "air" and urgency > 84 else rng.choice(["24 h", "36 h", "48 h", "60 h", "72 h", "96 h", "5 d", "6 d"])
            shipper = f"{rng.choice(shipper_prefixes)} {rng.choice(shipper_suffixes)}"
            origin = rng.choice(corridor["origins"])
            destination = rng.choice(corridor["destinations"])

            rows.append(
                {
                    "id": f"SHP-{shipment_number:05d}",
                    "corridor_id": corridor["id"],
                    "shipper": shipper,
                    "cargo": cargo,
                    "origin": origin,
                    "destination": destination,
                    "tonnes": tonnes,
                    "mode": mode,
                    "revenue_per_ton": revenue_per_ton,
                    "detour_km": detour_km,
                    "reliability": reliability,
                    "compatibility": compatibility,
                    "window": window,
                    "urgency": urgency,
                    "priority": rng.choice(["backhaul", "premium", "overflow", "return", "spot", "contract"]),
                    "pickup_window": pickup.isoformat(),
                    "delivery_window": delivery.isoformat(),
                }
            )
            shipment_number += 1
    return rows


def make_hubs(rng: random.Random) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, (name, city, state) in enumerate(HUB_CITIES, 1):
        dock_doors = rng.randint(8, 46)
        staging_tonnes = rng.randint(220, 2400)
        cold_capacity = rng.randint(0, 420)
        modes = rng.choice(["road", "road|staging", "road|air|staging", "road|sea|staging"])
        rows.append(
            {
                "id": f"HUB-{index:03d}",
                "name": name,
                "city": city,
                "state": state,
                "modes": modes,
                "dock_doors": dock_doors,
                "staging_tonnes": staging_tonnes,
                "cold_capacity_tonnes": cold_capacity,
                "reliability": rng.randint(78, 97),
            }
        )
    return rows


def make_partners(rng: random.Random) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    partner_types = ["transporter", "air-cargo", "shipping", "warehouse", "3pl"]
    regions = sorted({str(corridor["region"]) for corridor in CORRIDORS})
    for index in range(1, 145):
        partner_type = rng.choice(partner_types)
        if partner_type == "air-cargo":
            modes = "air|staging"
            fleet_size = rng.randint(2, 18)
        elif partner_type == "shipping":
            modes = "sea|staging"
            fleet_size = rng.randint(1, 12)
        elif partner_type == "warehouse":
            modes = "staging|road"
            fleet_size = rng.randint(1, 8)
        else:
            modes = "road|staging"
            fleet_size = rng.randint(12, 260)
        rows.append(
            {
                "id": f"PTR-{index:04d}",
                "name": f"{rng.choice(['Apex', 'Bharat', 'Crescent', 'Dakshin', 'Eastern', 'Frontier', 'Gateway', 'Harbour', 'Nexus', 'Pragati'])} {rng.choice(['Fleet', 'Cargo', 'Logistics', 'Freight', 'Supply', 'Carriers'])}",
                "type": partner_type,
                "home_region": rng.choice(regions),
                "modes": modes,
                "fleet_size": fleet_size,
                "on_time_percent": rng.randint(78, 98),
                "cancellation_rate_percent": round(rng.uniform(0.8, 8.5), 1),
                "claims_rate_percent": round(rng.uniform(0.1, 3.2), 1),
            }
        )
    return rows


def make_retail_rows() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    profiles: list[dict[str, object]] = []
    assortments: list[dict[str, object]] = []
    for profile in RETAIL_PROFILES:
        profiles.append(
            {
                "id": profile["id"],
                "name": profile["name"],
                "terminal": profile["terminal"],
                "passenger_mix": profile["passenger_mix"],
                "weekly_flights": profile["weekly_flights"],
                "base_revenue": profile["base_revenue"],
                "compliance": profile["compliance"],
            }
        )
        for label, share, uplift in profile["assortments"]:
            assortments.append(
                {
                    "retail_id": profile["id"],
                    "label": label,
                    "share": share,
                    "uplift": uplift,
                }
            )
    return profiles, assortments


def main() -> None:
    rng = random.Random(SEED)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    corridor_fields = [
        "id",
        "name",
        "anchor",
        "origin",
        "destination",
        "return_lane",
        "recurring",
        "distance_km",
        "baseline_empty_km",
        "base_anchor_tonnes",
        "vehicles",
        "service_level",
        "region",
    ]
    write_csv(DATA_DIR / "corridors.csv", corridor_fields, CORRIDORS)
    write_csv(
        DATA_DIR / "capacity.csv",
        ["corridor_id", "mode", "label", "capacity_tonnes", "available_percent", "status"],
        make_capacity_rows(rng),
    )
    write_csv(
        DATA_DIR / "shipments.csv",
        [
            "id",
            "corridor_id",
            "shipper",
            "cargo",
            "origin",
            "destination",
            "tonnes",
            "mode",
            "revenue_per_ton",
            "detour_km",
            "reliability",
            "compatibility",
            "window",
            "urgency",
            "priority",
            "pickup_window",
            "delivery_window",
        ],
        make_shipments(rng),
    )
    write_csv(
        DATA_DIR / "hubs.csv",
        [
            "id",
            "name",
            "city",
            "state",
            "modes",
            "dock_doors",
            "staging_tonnes",
            "cold_capacity_tonnes",
            "reliability",
        ],
        make_hubs(rng),
    )
    write_csv(
        DATA_DIR / "partners.csv",
        [
            "id",
            "name",
            "type",
            "home_region",
            "modes",
            "fleet_size",
            "on_time_percent",
            "cancellation_rate_percent",
            "claims_rate_percent",
        ],
        make_partners(rng),
    )
    retail_profiles, retail_assortments = make_retail_rows()
    write_csv(
        DATA_DIR / "retail_profiles.csv",
        ["id", "name", "terminal", "passenger_mix", "weekly_flights", "base_revenue", "compliance"],
        retail_profiles,
    )
    write_csv(
        DATA_DIR / "retail_assortments.csv",
        ["retail_id", "label", "share", "uplift"],
        retail_assortments,
    )

    print(f"Seeded dummy data in {DATA_DIR}")
    print(f"corridors={len(CORRIDORS)} shipments={len(CORRIDORS) * 200}")
    print(f"hubs={len(HUB_CITIES)} partners=144 retail_profiles={len(RETAIL_PROFILES)}")


if __name__ == "__main__":
    main()
