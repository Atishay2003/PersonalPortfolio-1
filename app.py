from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import DEFAULT_BUS_CAPACITY, DEFAULT_TARGET_LOAD_FACTOR, OUTPUT_DIR
from src.data_generator import ensure_dataset, load_routes
from src.model import metric_cards, predict_scenario, train_demand_model
from src.optimizer import concise_recommendations, optimize_network, summarize_network

st.set_page_config(
    page_title="Smart Public Transport Optimization",
    layout="wide",
)


@st.cache_data
def get_dataset() -> pd.DataFrame:
    return ensure_dataset()


@st.cache_data
def get_routes() -> pd.DataFrame:
    return load_routes()


@st.cache_resource
def get_model():
    return train_demand_model(get_dataset())


def save_dashboard_output(optimized_df: pd.DataFrame) -> Path:
    output_path = OUTPUT_DIR / "dashboard_recommendations.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    optimized_df.to_csv(output_path, index=False)
    return output_path


st.title("Smart Public Transport Optimization System")
st.caption(
    "Forecast demand, reduce overcrowding, and reassign buses where the city needs them most."
)

with st.sidebar:
    st.header("Scenario Inputs")
    selected_hour = st.slider("Hour", min_value=6, max_value=22, value=18)
    selected_day_type = st.selectbox("Day type", ["Weekday", "Weekend"])
    selected_weather = st.selectbox("Weather", ["Sunny", "Cloudy", "Rainy"], index=2)
    selected_special_event = st.selectbox("Special event", ["Yes", "No"])
    selected_total_fleet = st.slider("Total fleet available", min_value=8, max_value=60, value=41)
    selected_bus_capacity = st.slider(
        "Bus capacity", min_value=30, max_value=60, value=DEFAULT_BUS_CAPACITY
    )
    selected_target_load = st.slider(
        "Target load factor",
        min_value=0.60,
        max_value=0.95,
        value=DEFAULT_TARGET_LOAD_FACTOR,
        step=0.05,
    )

demand_df = get_dataset()
routes_df = get_routes()
model, metrics = get_model()

scenario_df = predict_scenario(
    model=model,
    routes_df=routes_df,
    hour=selected_hour,
    day_type=selected_day_type,
    weather=selected_weather,
    special_event=selected_special_event,
)
optimized_df = optimize_network(
    scenario_df=scenario_df,
    total_fleet=selected_total_fleet,
    bus_capacity=selected_bus_capacity,
    target_load_factor=selected_target_load,
)
summary = summarize_network(optimized_df, total_fleet=selected_total_fleet)
dashboard_output = save_dashboard_output(optimized_df)

metric_columns = st.columns(6)
metric_columns[0].metric("Predicted passengers/hr", summary["total_predicted_passengers"])
metric_columns[1].metric("Overcrowded before", summary["overcrowded_routes_before"])
metric_columns[2].metric("Overcrowded after", summary["overcrowded_routes_after"])
metric_columns[3].metric("Avg wait before", f"{summary['average_wait_before_minutes']} min")
metric_columns[4].metric("Avg wait after", f"{summary['average_wait_after_minutes']} min")
metric_columns[5].metric("Fleet used", summary["fleet_used"])

st.subheader("Model Quality")
model_cols = st.columns(3)
for idx, card in enumerate(metric_cards(metrics)):
    model_cols[idx].metric(card["label"], card["value"])

chart_col, table_col = st.columns((1.2, 1))

with chart_col:
    st.subheader("Demand by Route")
    route_chart = (
        optimized_df[["route_id", "predicted_demand"]]
        .sort_values("predicted_demand", ascending=False)
        .set_index("route_id")
    )
    st.bar_chart(route_chart)

    st.subheader("Load Factor Before vs After")
    load_chart = optimized_df[
        ["route_id", "current_load_factor", "recommended_load_factor"]
    ].set_index("route_id")
    st.line_chart(load_chart)

with table_col:
    st.subheader("Judge-Friendly Insights")
    for line in concise_recommendations(optimized_df, top_n=5):
        st.write(f"- {line}")

    st.subheader("Download Results")
    st.download_button(
        label="Download optimized schedule CSV",
        data=optimized_df.to_csv(index=False).encode("utf-8"),
        file_name="optimized_schedule.csv",
        mime="text/csv",
    )
    st.caption(f"Latest dashboard export saved to `{dashboard_output}`")

st.subheader("Optimized Route Table")
st.dataframe(
    optimized_df[
        [
            "route_id",
            "route_name",
            "zone",
            "predicted_demand",
            "current_buses",
            "recommended_buses",
            "bus_change",
            "current_headway_minutes",
            "recommended_headway_minutes",
            "risk_before",
            "risk_after",
            "action",
        ]
    ],
    use_container_width=True,
)

with st.expander("Training Data Snapshot"):
    st.dataframe(demand_df.head(20), use_container_width=True)

with st.expander("Why this can win a hackathon"):
    st.markdown(
        """
        - It solves crowding, delays, and fleet under-utilization with one platform.
        - It mixes AI forecasting with operational decision support.
        - It gives route-level action items instead of only charts.
        - It is easy to extend with GPS, ticketing data, IoT counters, and city dashboards.
        """
    )
