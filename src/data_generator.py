from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.config import (
    DATA_DIR,
    DEFAULT_BUS_CAPACITY,
    DEFAULT_END_DATE,
    DEFAULT_START_DATE,
    DEMAND_PATH,
    OPERATING_HOURS,
    RANDOM_STATE,
    ROUTES_PATH,
)

HOUR_MULTIPLIER = {
    6: 0.75,
    7: 1.15,
    8: 1.40,
    9: 1.20,
    10: 0.95,
    11: 0.90,
    12: 1.00,
    13: 0.92,
    14: 0.88,
    15: 0.95,
    16: 1.10,
    17: 1.30,
    18: 1.45,
    19: 1.25,
    20: 1.00,
    21: 0.82,
    22: 0.65,
}

WEEKEND_ZONE_MULTIPLIER = {
    "CBD": 0.90,
    "University": 0.62,
    "Commercial": 1.12,
    "Airport": 1.08,
    "Industrial": 0.70,
    "Healthcare": 1.00,
    "Residential": 0.92,
    "Entertainment": 1.35,
}

WEATHER_MULTIPLIER = {"Sunny": 1.00, "Cloudy": 1.04, "Rainy": 1.16}
EVENT_BOOST = {
    "CBD": 1.22,
    "University": 1.14,
    "Commercial": 1.18,
    "Airport": 1.06,
    "Industrial": 1.02,
    "Healthcare": 1.05,
    "Residential": 1.08,
    "Entertainment": 1.35,
}


def load_routes(routes_path: Path = ROUTES_PATH) -> pd.DataFrame:
    return pd.read_csv(routes_path)


def _sample_weather(rng: np.random.Generator) -> str:
    return rng.choice(["Sunny", "Cloudy", "Rainy"], p=[0.56, 0.24, 0.20]).item()


def _sample_special_event(rng: np.random.Generator, date: pd.Timestamp, hour: int) -> str:
    base_probability = 0.04
    if date.dayofweek in (4, 5) and hour >= 17:
        base_probability += 0.10
    if hour in (12, 13, 18, 19):
        base_probability += 0.03
    return "Yes" if rng.random() < base_probability else "No"


def generate_passenger_demand(
    routes_df: pd.DataFrame,
    start_date: str = DEFAULT_START_DATE,
    end_date: str = DEFAULT_END_DATE,
    random_state: int = RANDOM_STATE,
) -> pd.DataFrame:
    rng = np.random.default_rng(random_state)
    dates = pd.date_range(start=start_date, end=end_date, freq="D")
    records: list[dict[str, object]] = []

    for route in routes_df.itertuples(index=False):
        for date in dates:
            day_type = "Weekend" if date.dayofweek >= 5 else "Weekday"
            for hour in OPERATING_HOURS:
                weather = _sample_weather(rng)
                special_event = _sample_special_event(rng, date, hour)

                demand = route.base_demand
                demand *= HOUR_MULTIPLIER[hour]
                demand *= WEATHER_MULTIPLIER[weather]

                if day_type == "Weekend":
                    demand *= WEEKEND_ZONE_MULTIPLIER[route.zone]

                if special_event == "Yes":
                    demand *= EVENT_BOOST[route.zone]

                if route.zone == "Airport" and hour in (6, 7, 20, 21):
                    demand *= 1.12
                if route.zone == "Healthcare" and day_type == "Weekend":
                    demand *= 1.05
                if route.zone == "Industrial" and hour >= 18:
                    demand *= 0.82

                noise = rng.normal(loc=0.0, scale=12.0)
                passenger_demand = max(20, int(round(demand + noise)))

                current_capacity = (
                    route.current_buses * (60 / route.round_trip_minutes) * DEFAULT_BUS_CAPACITY
                )

                records.append(
                    {
                        "date": date.date().isoformat(),
                        "route_id": route.route_id,
                        "route_name": route.route_name,
                        "origin": route.origin,
                        "destination": route.destination,
                        "zone": route.zone,
                        "hour": hour,
                        "day_type": day_type,
                        "weather": weather,
                        "special_event": special_event,
                        "base_demand": route.base_demand,
                        "current_buses": route.current_buses,
                        "round_trip_minutes": route.round_trip_minutes,
                        "current_capacity_per_hour": round(current_capacity, 2),
                        "occupancy_ratio": round(passenger_demand / current_capacity, 3),
                        "passenger_demand": passenger_demand,
                    }
                )

    return pd.DataFrame(records)


def create_dataset(
    routes_path: Path = ROUTES_PATH,
    output_path: Path = DEMAND_PATH,
    start_date: str = DEFAULT_START_DATE,
    end_date: str = DEFAULT_END_DATE,
    random_state: int = RANDOM_STATE,
) -> pd.DataFrame:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    routes_df = load_routes(routes_path)
    demand_df = generate_passenger_demand(
        routes_df=routes_df,
        start_date=start_date,
        end_date=end_date,
        random_state=random_state,
    )
    demand_df.to_csv(output_path, index=False)
    return demand_df


def ensure_dataset(output_path: Path = DEMAND_PATH) -> pd.DataFrame:
    if output_path.exists():
        return pd.read_csv(output_path)
    return create_dataset(output_path=output_path)
