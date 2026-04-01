from __future__ import annotations

from typing import Any

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from src.config import RANDOM_STATE

CATEGORICAL_FEATURES = ["route_id", "zone", "day_type", "weather", "special_event"]
NUMERIC_FEATURES = ["hour", "base_demand", "current_buses", "round_trip_minutes"]
FEATURE_COLUMNS = CATEGORICAL_FEATURES + NUMERIC_FEATURES


def train_demand_model(demand_df: pd.DataFrame) -> tuple[Pipeline, dict[str, float]]:
    X = demand_df[FEATURE_COLUMNS]
    y = demand_df["passenger_demand"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=RANDOM_STATE,
    )

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                CATEGORICAL_FEATURES,
            ),
            ("numeric", "passthrough", NUMERIC_FEATURES),
        ]
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "regressor",
                RandomForestRegressor(
                    n_estimators=250,
                    max_depth=14,
                    min_samples_leaf=2,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )

    pipeline.fit(X_train, y_train)
    predictions = pipeline.predict(X_test)

    metrics = {
        "mae": round(mean_absolute_error(y_test, predictions), 2),
        "rmse": round(mean_squared_error(y_test, predictions, squared=False), 2),
        "r2": round(r2_score(y_test, predictions), 3),
    }
    return pipeline, metrics


def build_scenario_frame(
    routes_df: pd.DataFrame,
    hour: int,
    day_type: str,
    weather: str,
    special_event: str,
) -> pd.DataFrame:
    scenario_df = routes_df.copy()
    scenario_df["hour"] = hour
    scenario_df["day_type"] = day_type
    scenario_df["weather"] = weather
    scenario_df["special_event"] = special_event
    return scenario_df


def predict_scenario(
    model: Pipeline,
    routes_df: pd.DataFrame,
    hour: int,
    day_type: str,
    weather: str,
    special_event: str,
) -> pd.DataFrame:
    scenario_df = build_scenario_frame(
        routes_df=routes_df,
        hour=hour,
        day_type=day_type,
        weather=weather,
        special_event=special_event,
    )
    scenario_df["predicted_demand"] = (
        model.predict(scenario_df[FEATURE_COLUMNS]).round().astype(int)
    )
    return scenario_df


def metric_cards(metrics: dict[str, float]) -> list[dict[str, Any]]:
    return [
        {"label": "Model MAE", "value": metrics["mae"]},
        {"label": "Model RMSE", "value": metrics["rmse"]},
        {"label": "Model R2", "value": metrics["r2"]},
    ]
