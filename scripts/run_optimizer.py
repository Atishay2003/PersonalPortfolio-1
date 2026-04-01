from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DEFAULT_BUS_CAPACITY, DEFAULT_TARGET_LOAD_FACTOR, OUTPUT_DIR
from src.data_generator import ensure_dataset, load_routes
from src.model import predict_scenario, train_demand_model
from src.optimizer import concise_recommendations, optimize_network, summarize_network
from src.reporting import save_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Smart Public Transport Optimization System."
    )
    parser.add_argument("--hour", type=int, default=18, help="Hour of the day (6-22).")
    parser.add_argument(
        "--day-type",
        default="Weekday",
        choices=["Weekday", "Weekend"],
        help="Choose Weekday or Weekend.",
    )
    parser.add_argument(
        "--weather",
        default="Rainy",
        choices=["Sunny", "Cloudy", "Rainy"],
        help="Weather condition for the scenario.",
    )
    parser.add_argument(
        "--special-event",
        default="Yes",
        choices=["Yes", "No"],
        help="Whether there is a special event near key zones.",
    )
    parser.add_argument(
        "--total-fleet",
        type=int,
        default=41,
        help="Total number of buses available across the city.",
    )
    parser.add_argument(
        "--bus-capacity",
        type=int,
        default=DEFAULT_BUS_CAPACITY,
        help="Passengers each bus can carry per trip.",
    )
    parser.add_argument(
        "--target-load-factor",
        type=float,
        default=DEFAULT_TARGET_LOAD_FACTOR,
        help="Target occupancy threshold below which crowding is acceptable.",
    )
    parser.add_argument(
        "--csv-output",
        default=str(OUTPUT_DIR / "optimized_schedule.csv"),
        help="Path to save route-level recommendations as CSV.",
    )
    parser.add_argument(
        "--summary-output",
        default=str(OUTPUT_DIR / "network_summary.json"),
        help="Path to save the network summary as JSON.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    demand_df = ensure_dataset()
    routes_df = load_routes()
    model, metrics = train_demand_model(demand_df)
    scenario_df = predict_scenario(
        model=model,
        routes_df=routes_df,
        hour=args.hour,
        day_type=args.day_type,
        weather=args.weather,
        special_event=args.special_event,
    )
    optimized_df = optimize_network(
        scenario_df=scenario_df,
        total_fleet=args.total_fleet,
        bus_capacity=args.bus_capacity,
        target_load_factor=args.target_load_factor,
    )
    summary = summarize_network(optimized_df, total_fleet=args.total_fleet)
    save_outputs(
        optimized_df=optimized_df,
        summary=summary,
        csv_path=Path(args.csv_output),
        json_path=Path(args.summary_output),
    )

    print("=== Smart Public Transport Optimization System ===")
    print(
        f"Scenario: hour={args.hour}, day_type={args.day_type}, "
        f"weather={args.weather}, special_event={args.special_event}"
    )
    print(
        f"Model quality -> MAE: {metrics['mae']}, RMSE: {metrics['rmse']}, R2: {metrics['r2']}"
    )
    print(
        "Network summary -> "
        f"Passengers: {summary['total_predicted_passengers']}, "
        f"Overcrowded routes before: {summary['overcrowded_routes_before']}, "
        f"after: {summary['overcrowded_routes_after']}, "
        f"Average wait before: {summary['average_wait_before_minutes']} min, "
        f"after: {summary['average_wait_after_minutes']} min"
    )
    print("\nTop recommendations:")
    for line in concise_recommendations(optimized_df, top_n=5):
        print(f"- {line}")
    print(f"\nCSV saved to: {args.csv_output}")
    print(f"Summary saved to: {args.summary_output}")


if __name__ == "__main__":
    main()
