from __future__ import annotations

import unittest

from clustering import build_shipment_cluster_lookup
from optimizer import optimise_corridor, rank_air_carriers
from repository import find_corridor, load_dataset


class CapacityIQBackendTest(unittest.TestCase):
    def test_dataset_has_realistic_volume(self) -> None:
        dataset = load_dataset()
        counts = dataset["rawCounts"]

        self.assertGreaterEqual(counts["corridors"], 10)
        self.assertGreaterEqual(counts["shipments"], 2000)
        self.assertGreaterEqual(counts["hubs"], 40)
        self.assertGreaterEqual(counts["partners"], 100)
        self.assertGreaterEqual(counts["retailProfiles"], 8)
        self.assertGreaterEqual(counts["airCarriers"], 5)

    def test_corridors_have_capacity_and_shipments(self) -> None:
        dataset = load_dataset()

        for corridor in dataset["corridors"]:
            self.assertGreaterEqual(len(corridor["modes"]), 4)
            self.assertGreaterEqual(len(corridor["shipments"]), 100)
            first_shipment = corridor["shipments"][0]
            self.assertIn("cargoFamily", first_shipment)
            self.assertIn("vehicleProfile", first_shipment)
            self.assertIn("driverScore", first_shipment)
            self.assertIn("contractType", first_shipment)

    def test_retail_profiles_include_clearance_assumptions(self) -> None:
        dataset = load_dataset()
        profiles = dataset["retailProfiles"]
        domestic_profile = next(profile for profile in profiles if profile["id"] == "domestic-metro")
        international_profiles = [profile for profile in profiles if profile["routeType"] == "international"]

        self.assertGreaterEqual(len(international_profiles), 1)
        self.assertEqual(domestic_profile["routeType"], "domestic")
        self.assertEqual(domestic_profile["immigrationMinutes"], 0)
        self.assertGreater(international_profiles[0]["securityMinutes"], domestic_profile["securityMinutes"])
        self.assertGreater(international_profiles[0]["recommendedArrivalMinutes"], domestic_profile["recommendedArrivalMinutes"])

    def test_optimiser_returns_business_metrics(self) -> None:
        dataset = load_dataset()
        corridor = find_corridor("northeast")
        self.assertIsNotNone(corridor)

        result = optimise_corridor(
            corridor,
            anchor_enabled=True,
            anchor_multiplier=1.0,
            max_detour=120,
            guardrail=74,
            cluster_lookup=build_shipment_cluster_lookup(dataset),
            air_carriers=dataset["airCarriers"],
            air_price_priority=60,
        )

        self.assertGreater(result["matchedTonnes"], 0)
        self.assertGreater(result["revenue"], 0)
        self.assertGreater(result["emptyKmAvoided"], 0)
        self.assertIn("operationalSummary", result)
        self.assertGreater(result["operationalSummary"]["avgDriverScore"], 0)
        self.assertGreater(result["operationalSummary"]["avgClusterFit"], 0)
        self.assertGreaterEqual(result["operationalSummary"]["clusterBoostedMatches"], 0)
        self.assertIn("road", result["remaining"])
        self.assertGreater(len(result["accepted"]), 0)
        self.assertIn("clusterLabel", result["accepted"][0])
        self.assertIn("clusterFit", result["accepted"][0])
        self.assertGreater(len(result["recommendedActions"]), 0)
        first_action = result["recommendedActions"][0]
        self.assertGreater(first_action["matchedTonnes"], 0)
        self.assertGreater(first_action["revenue"], 0)
        self.assertGreaterEqual(len(first_action["route"]), 2)
        self.assertIn("assignedVehicle", first_action)
        self.assertIn("schedulePlan", first_action)
        self.assertIn("clusterLabel", first_action)

    def test_air_carrier_price_and_location_tradeoff(self) -> None:
        dataset = load_dataset()
        air_shipment = next(
            shipment
            for corridor in dataset["corridors"]
            for shipment in corridor["shipments"]
            if shipment["mode"] == "air" and shipment["compatibility"] == "regulated"
        )
        fastest_first = rank_air_carriers(
            "northeast", air_shipment, dataset["airCarriers"], price_priority=0
        )
        cheapest_first = rank_air_carriers(
            "northeast", air_shipment, dataset["airCarriers"], price_priority=100
        )

        self.assertGreaterEqual(len(fastest_first), 2)
        self.assertLessEqual(cheapest_first[0]["estimatedCost"], fastest_first[0]["estimatedCost"])
        self.assertIn("totalClearanceMinutes", cheapest_first[0])
        self.assertIn("tradeoff", cheapest_first[0])

    def test_kmeans_lookup_covers_shipments_used_by_optimizer(self) -> None:
        dataset = load_dataset()
        lookup = build_shipment_cluster_lookup(dataset)

        self.assertGreaterEqual(len(lookup), 2000)
        first_shipment = dataset["corridors"][0]["shipments"][0]
        profile = lookup[first_shipment["id"]]
        self.assertIn("label", profile)
        self.assertIn("fit", profile)
        self.assertIn("adjustment", profile)
        self.assertIn("insight", profile)


if __name__ == "__main__":
    unittest.main()
