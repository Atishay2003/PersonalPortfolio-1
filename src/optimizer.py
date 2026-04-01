from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import DEFAULT_BUS_CAPACITY, DEFAULT_TARGET_LOAD_FACTOR


def _capacity_for_route(
    buses: float | np.ndarray,
    round_trip_minutes: float | np.ndarray,
    bus_capacity: int,
) -> np.ndarray:
    safe_buses = np.maximum(np.asarray(buses, dtype=float), 1.0)
    safe_minutes = np.maximum(np.asarray(round_trip_minutes, dtype=float), 1.0)
    return safe_buses * (60 / safe_minutes) * bus_capacity


def _route_risk(
    demand: float,
    buses: int,
    round_trip_minutes: float,
    bus_capacity: int,
    target_load_factor: float,
) -> float:
    load_factor = demand / _capacity_for_route(buses, round_trip_minutes, bus_capacity)
    return max(float(load_factor) - target_load_factor, 0.0) ** 2


def _normalize_total_fleet(
    allocated: np.ndarray,
    demand: np.ndarray,
    round_trip_minutes: np.ndarray,
    total_fleet: int,
    bus_capacity: int,
    target_load_factor: float,
) -> np.ndarray:
    allocated = allocated.astype(int)

    while allocated.sum() < total_fleet:
        risks = np.array(
            [
                _route_risk(d, b, m, bus_capacity, target_load_factor)
                for d, b, m in zip(demand, allocated, round_trip_minutes)
            ]
        )
        idx = int(np.argmax(risks))
        allocated[idx] += 1

    while allocated.sum() > total_fleet:
        candidate_indices = np.where(allocated > 1)[0]
        removal_costs = []
        for idx in candidate_indices:
            removal_costs.append(
                _route_risk(
                    demand[idx],
                    allocated[idx] - 1,
                    round_trip_minutes[idx],
                    bus_capacity,
                    target_load_factor,
                )
            )
        idx = int(candidate_indices[int(np.argmin(removal_costs))])
        allocated[idx] -= 1

    return allocated


def _improve_by_transfers(
    allocated: np.ndarray,
    demand: np.ndarray,
    round_trip_minutes: np.ndarray,
    bus_capacity: int,
    target_load_factor: float,
) -> np.ndarray:
    max_iterations = len(allocated) * 20

    for _ in range(max_iterations):
        current_risks = np.array(
            [
                _route_risk(d, b, m, bus_capacity, target_load_factor)
                for d, b, m in zip(demand, allocated, round_trip_minutes)
            ]
        )
        best_gain = 0.0
        best_pair: tuple[int, int] | None = None

        for donor in range(len(allocated)):
            if allocated[donor] <= 1:
                continue

            donor_cost = _route_risk(
                demand[donor],
                allocated[donor] - 1,
                round_trip_minutes[donor],
                bus_capacity,
                target_load_factor,
            ) - current_risks[donor]

            for receiver in range(len(allocated)):
                if receiver == donor:
                    continue

                receiver_benefit = current_risks[receiver] - _route_risk(
                    demand[receiver],
                    allocated[receiver] + 1,
                    round_trip_minutes[receiver],
                    bus_capacity,
                    target_load_factor,
                )
                gain = receiver_benefit - donor_cost
                if gain > best_gain + 1e-9:
                    best_gain = gain
                    best_pair = (donor, receiver)

        if not best_pair:
            break

        donor, receiver = best_pair
        allocated[donor] -= 1
        allocated[receiver] += 1

    return allocated


def _risk_label(load_factor: float, target_load_factor: float) -> str:
    if load_factor > 1.0:
        return "High"
    if load_factor > target_load_factor:
        return "Medium"
    return "Low"


def optimize_network(
    scenario_df: pd.DataFrame,
    total_fleet: int,
    bus_capacity: int = DEFAULT_BUS_CAPACITY,
    target_load_factor: float = DEFAULT_TARGET_LOAD_FACTOR,
) -> pd.DataFrame:
    if total_fleet < len(scenario_df):
        raise ValueError(
            f"Total fleet must be at least {len(scenario_df)} so every route gets one bus."
        )

    result_df = scenario_df.copy()
    demand = result_df["predicted_demand"].to_numpy(dtype=float)
    round_trip_minutes = result_df["round_trip_minutes"].to_numpy(dtype=float)
    allocated = result_df["current_buses"].to_numpy(dtype=int)

    allocated = _normalize_total_fleet(
        allocated=allocated,
        demand=demand,
        round_trip_minutes=round_trip_minutes,
        total_fleet=total_fleet,
        bus_capacity=bus_capacity,
        target_load_factor=target_load_factor,
    )
    allocated = _improve_by_transfers(
        allocated=allocated,
        demand=demand,
        round_trip_minutes=round_trip_minutes,
        bus_capacity=bus_capacity,
        target_load_factor=target_load_factor,
    )

    current_capacity = _capacity_for_route(
        result_df["current_buses"], result_df["round_trip_minutes"], bus_capacity
    )
    recommended_capacity = _capacity_for_route(
        allocated, result_df["round_trip_minutes"], bus_capacity
    )
    current_load_factor = result_df["predicted_demand"] / current_capacity
    recommended_load_factor = result_df["predicted_demand"] / recommended_capacity
    service_rate_per_bus = (60 / result_df["round_trip_minutes"]) * bus_capacity

    result_df["ideal_buses"] = np.ceil(
        result_df["predicted_demand"] / (service_rate_per_bus * target_load_factor)
    ).clip(lower=1).astype(int)
    result_df["recommended_buses"] = allocated.astype(int)
    result_df["bus_change"] = result_df["recommended_buses"] - result_df["current_buses"]
    result_df["current_capacity_per_hour"] = current_capacity.round(2)
    result_df["recommended_capacity_per_hour"] = recommended_capacity.round(2)
    result_df["current_load_factor"] = current_load_factor.round(2)
    result_df["recommended_load_factor"] = recommended_load_factor.round(2)
    result_df["current_headway_minutes"] = (
        result_df["round_trip_minutes"] / result_df["current_buses"]
    ).round(1)
    result_df["recommended_headway_minutes"] = (
        result_df["round_trip_minutes"] / result_df["recommended_buses"]
    ).round(1)
    result_df["risk_before"] = [
        _risk_label(load, target_load_factor) for load in current_load_factor
    ]
    result_df["risk_after"] = [
        _risk_label(load, target_load_factor) for load in recommended_load_factor
    ]

    result_df["action"] = "Keep current service"
    result_df.loc[result_df["bus_change"] > 0, "action"] = "Increase service"
    result_df.loc[result_df["bus_change"] < 0, "action"] = "Reassign buses"
    result_df["priority_score"] = (
        result_df["predicted_demand"] * result_df["recommended_load_factor"]
    ).round(2)

    return result_df.sort_values(
        by=["predicted_demand", "recommended_load_factor"],
        ascending=[False, False],
    ).reset_index(drop=True)


def summarize_network(
    optimized_df: pd.DataFrame,
    total_fleet: int,
) -> dict[str, float]:
    return {
        "total_predicted_passengers": int(optimized_df["predicted_demand"].sum()),
        "overcrowded_routes_before": int((optimized_df["current_load_factor"] > 1.0).sum()),
        "overcrowded_routes_after": int((optimized_df["recommended_load_factor"] > 1.0).sum()),
        "average_wait_before_minutes": round(
            float((optimized_df["current_headway_minutes"] / 2).mean()), 1
        ),
        "average_wait_after_minutes": round(
            float((optimized_df["recommended_headway_minutes"] / 2).mean()), 1
        ),
        "fleet_used": int(optimized_df["recommended_buses"].sum()),
        "reserve_buses": int(total_fleet - optimized_df["recommended_buses"].sum()),
    }


def concise_recommendations(optimized_df: pd.DataFrame, top_n: int = 3) -> list[str]:
    lines: list[str] = []
    for row in optimized_df.head(top_n).itertuples(index=False):
        if row.bus_change > 0:
            action = f"add {row.bus_change} bus(es)"
        elif row.bus_change < 0:
            action = f"reassign {abs(row.bus_change)} bus(es)"
        else:
            action = "keep fleet unchanged"

        lines.append(
            f"{row.route_id} {row.route_name}: demand {row.predicted_demand}/hr, "
            f"{action}, headway {row.current_headway_minutes} -> {row.recommended_headway_minutes} min."
        )
    return lines
