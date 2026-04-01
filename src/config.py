from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
ROUTES_PATH = DATA_DIR / "routes.csv"
DEMAND_PATH = DATA_DIR / "passenger_demand.csv"

RANDOM_STATE = 42
DEFAULT_BUS_CAPACITY = 40
DEFAULT_TARGET_LOAD_FACTOR = 0.85
OPERATING_HOURS = list(range(6, 23))
DEFAULT_START_DATE = "2026-01-01"
DEFAULT_END_DATE = "2026-03-15"
