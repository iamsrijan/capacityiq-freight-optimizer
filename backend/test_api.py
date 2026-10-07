from __future__ import annotations

import unittest

from clustering import build_clusters
from optimizer import optimise_corridor
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

    def test_optimiser_returns_business_metrics(self) -> None:
        corridor = find_corridor("northeast")
        self.assertIsNotNone(corridor)

        result = optimise_corridor(
            corridor,
            anchor_enabled=True,
            anchor_multiplier=1.0,
            max_detour=120,
            guardrail=74,
        )

        self.assertGreater(result["matchedTonnes"], 0)
        self.assertGreater(result["revenue"], 0)
        self.assertGreater(result["emptyKmAvoided"], 0)
        self.assertIn("operationalSummary", result)
        self.assertGreater(result["operationalSummary"]["avgDriverScore"], 0)
        self.assertIn("road", result["remaining"])
        self.assertGreater(len(result["accepted"]), 0)
        self.assertGreater(len(result["recommendedActions"]), 0)
        first_action = result["recommendedActions"][0]
        self.assertGreater(first_action["matchedTonnes"], 0)
        self.assertGreater(first_action["revenue"], 0)
        self.assertGreaterEqual(len(first_action["route"]), 2)
        self.assertIn("assignedVehicle", first_action)
        self.assertIn("schedulePlan", first_action)

    def test_kmeans_clusters_cover_operational_domains(self) -> None:
        dataset = load_dataset()
        clusters = build_clusters(dataset)
        domains = {domain["domain"]: domain for domain in clusters["domains"]}

        self.assertEqual(
            {"routes", "customers", "shipments", "vehicles", "passengers"},
            set(domains.keys()),
        )
        for domain in domains.values():
            self.assertGreaterEqual(len(domain["clusters"]), 3)
            self.assertGreater(len(domain["features"]), 0)
            self.assertGreater(domain["clusters"][0]["size"], 0)
            self.assertIn("insight", domain["clusters"][0])


if __name__ == "__main__":
    unittest.main()
