from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.optimizer import optimize_network


class OptimizerTestCase(unittest.TestCase):
    def test_optimizer_respects_total_fleet(self) -> None:
        scenario_df = pd.DataFrame(
            {
                "route_id": ["R1", "R2", "R3"],
                "route_name": ["A", "B", "C"],
                "zone": ["CBD", "University", "Residential"],
                "predicted_demand": [300, 150, 120],
                "current_buses": [3, 2, 1],
                "round_trip_minutes": [60, 50, 45],
                "base_demand": [120, 90, 70],
            }
        )

        optimized_df = optimize_network(scenario_df=scenario_df, total_fleet=6)

        self.assertEqual(int(optimized_df["recommended_buses"].sum()), 6)
        self.assertTrue((optimized_df["recommended_buses"] >= 1).all())
        top_route = optimized_df.loc[optimized_df["route_id"] == "R1"].iloc[0]
        self.assertGreaterEqual(int(top_route["recommended_buses"]), 3)


if __name__ == "__main__":
    unittest.main()
