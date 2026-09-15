from __future__ import annotations

import unittest

import server


class CapacityIQBackendTest(unittest.TestCase):
    def test_dataset_has_realistic_volume(self) -> None:
        dataset = server.load_dataset()
        counts = dataset["rawCounts"]

        self.assertGreaterEqual(counts["corridors"], 10)
        self.assertGreaterEqual(counts["shipments"], 2000)
        self.assertGreaterEqual(counts["hubs"], 40)
        self.assertGreaterEqual(counts["partners"], 100)
        self.assertGreaterEqual(counts["retailProfiles"], 8)

    def test_corridors_have_capacity_and_shipments(self) -> None:
        dataset = server.load_dataset()

        for corridor in dataset["corridors"]:
            self.assertGreaterEqual(len(corridor["modes"]), 4)
            self.assertGreaterEqual(len(corridor["shipments"]), 100)

    def test_optimiser_returns_business_metrics(self) -> None:
        corridor = server.find_corridor("northeast")
        self.assertIsNotNone(corridor)

        result = server.optimise_corridor(
            corridor,
            anchor_enabled=True,
            anchor_multiplier=1.0,
            max_detour=120,
            guardrail=74,
        )

        self.assertGreater(result["matchedTonnes"], 0)
        self.assertGreater(result["revenue"], 0)
        self.assertGreater(result["emptyKmAvoided"], 0)
        self.assertIn("road", result["remaining"])
        self.assertGreater(len(result["accepted"]), 0)


if __name__ == "__main__":
    unittest.main()
