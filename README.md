# Smart Public Transport Optimization System

This project is a Python-based hackathon solution for the **Smart City** track. It predicts passenger demand and recommends how to optimize bus routes, schedules, and fleet distribution so the city can reduce crowding and improve reliability.

## Why this project is strong

- It solves a real problem with a practical flow: **forecast -> optimize -> visualize -> act**.
- It combines **machine learning** and **operations planning**, which makes it stronger than a basic dashboard.
- It gives judges clear outputs:
  - Which route is likely to be overcrowded
  - How many buses should be reassigned
  - How average waiting time changes
  - How the city can later connect GPS and ticketing data

## Project structure

```text
smart_transport_optimizer/
|-- app.py
|-- requirements.txt
|-- README.md
|-- .streamlit/config.toml
|-- data/
|   |-- routes.csv
|   |-- passenger_demand.csv
|-- outputs/
|   |-- optimized_schedule.csv
|   |-- network_summary.json
|   |-- dashboard_recommendations.csv
|-- scripts/
|   |-- generate_data.py
|   |-- run_optimizer.py
|-- src/
|   |-- config.py
|   |-- data_generator.py
|   |-- model.py
|   |-- optimizer.py
|   |-- reporting.py
|-- tests/
|   |-- test_optimizer.py
```

## Input and output

### Inputs

1. Historical and synthetic route data from `data/routes.csv` and `data/passenger_demand.csv`
2. Scenario inputs chosen by the user:
   - `hour`
   - `day_type`
   - `weather`
   - `special_event`
   - `total_fleet`
   - `bus_capacity`
   - `target_load_factor`

### Outputs

- Route-wise demand prediction
- Recommended buses per route
- Current vs optimized headway
- Overcrowding risk before and after
- CSV report in `outputs/optimized_schedule.csv`
- JSON summary in `outputs/network_summary.json`

## Step-by-step Windows CMD guide

Open **Command Prompt** and run these commands one by one.

### 1. Move to the project folder

```cmd
cd /d "C:\Users\atish\OneDrive\Documents(1)\New project\smart_transport_optimizer"
```

### 2. Create a virtual environment

```cmd
python -m venv .venv
```

### 3. Activate the virtual environment

```cmd
.venv\Scripts\activate
```

### 4. Install Python packages

```cmd
python -m pip install -r requirements.txt
```

### 5. Generate the passenger-demand dataset

```cmd
python scripts\generate_data.py
```

Expected output:

```text
Dataset created at: ...\smart_transport_optimizer\data\passenger_demand.csv
Rows: 10064
Routes: 8
Columns: route_id, hour, day_type, weather, special_event, passenger_demand
```

### 6. Run the optimizer from the command line

```cmd
python scripts\run_optimizer.py --hour 18 --day-type Weekday --weather Rainy --special-event Yes --total-fleet 41
```

Expected output:

```text
=== Smart Public Transport Optimization System ===
Scenario: hour=18, day_type=Weekday, weather=Rainy, special_event=Yes
Model quality -> MAE: 10.38, RMSE: 13.09, R2: 0.842
Network summary -> Passengers: 1404, Overcrowded routes before: 2, after: 0, Average wait before: 6.1 min, after: 5.4 min
```

### 7. Start the dashboard

```cmd
streamlit run app.py
```

After that, your browser will open a local dashboard where you can change conditions such as rain, peak hour, weekend, and special events.

### 8. Run the test

```cmd
python -m unittest tests\test_optimizer.py
```

## How the system works

1. `scripts/generate_data.py` creates historical passenger demand using route details, time of day, weather, and event patterns.
2. `src/model.py` trains a `RandomForestRegressor` to predict route demand.
3. `scripts/run_optimizer.py` creates a scenario and predicts demand for each route.
4. `src/optimizer.py` reallocates buses across routes to reduce overcrowding while respecting the total fleet size.
5. `app.py` visualizes the results in a dashboard.

## Demo scenario to show judges

Use this exact demo:

- Hour: `18`
- Day type: `Weekday`
- Weather: `Rainy`
- Special event: `Yes`
- Total fleet: `41`

Tell the judges:

- Rainy evening rush causes a sudden passenger spike.
- The model predicts which routes will get crowded.
- The optimizer shifts buses from lower-pressure routes to high-pressure routes.
- The city gets lower wait times and reduces overcrowded routes from `2` to `0` without buying a new fleet.

## Deployment

### Option 1: Streamlit Community Cloud

1. Create a GitHub repository and push the `smart_transport_optimizer` folder.
2. Make sure the repository contains:
   - `app.py`
   - `requirements.txt`
   - `data/routes.csv`
3. In Streamlit Community Cloud, create a new app and select:
   - Repository: your GitHub repo
   - Branch: `main`
   - Main file path: `app.py`
4. In Advanced settings, choose Python `3.11` so it matches the version tested locally.
5. Click deploy.

## Future improvements

- Add GPS-based live bus tracking
- Connect with smart-card or QR ticketing data
- Add a map view with route heatmaps
- Use reinforcement learning for dynamic dispatching
- Add a driver and depot scheduling module

## Short presentation line

**"Our system helps a smart city predict crowding before it happens and dynamically redistribute buses to the routes that need them most."**
