from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def save_outputs(
    optimized_df: pd.DataFrame,
    summary: dict[str, float],
    csv_path: Path,
    json_path: Path,
) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    optimized_df.to_csv(csv_path, index=False)
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
