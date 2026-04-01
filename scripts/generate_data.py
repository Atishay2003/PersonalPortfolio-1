from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DEMAND_PATH
from src.data_generator import create_dataset


def main() -> None:
    demand_df = create_dataset()
    print(f"Dataset created at: {DEMAND_PATH}")
    print(f"Rows: {len(demand_df)}")
    print(f"Routes: {demand_df['route_id'].nunique()}")
    print("Columns: route_id, hour, day_type, weather, special_event, passenger_demand")


if __name__ == "__main__":
    main()
