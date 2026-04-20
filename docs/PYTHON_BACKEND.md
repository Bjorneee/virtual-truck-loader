# Python Backend Documentation

## Overview
The Python backend provides:
- A REST API for Unity
- Data validation
- Packing/optimization logic
- Developer-Only Testing Simulation

## Folder Structure
python/  
│   dev-requirements.txt
│   README.md
│   requirements.txt
│
├───api
│   │   config.py
│   │   logging.py
│   │   main.py
│   │   routes.py
│   └── schemas.py
│
├───dev_renderer
│   │   main.py
│   │   vconfig.py
│   │
│   ├───app
│   │   │   api_client.py
│   │   │   loader.py
│   │   └── viewer.py
│   │
│   ├───camera
│   │   └──camera.py
│   │
│   ├───scene
│   │   │   grid.py
│   │   │   ground.py
│   │   │   lighting.py
│   │   └── primitives.py
│   │
│   └───utils
│       │   helpers.py
│       └── json_loader.py
│
├───services
│   └── packing_services.py
│
├───tests
│   │   0_axis.json
│   │   10_many_small.json
│   │   11_fragmentation.json
│   │   12_flat.json
│   │   13_single_type.json
│   │   1_simple.json
│   │   2_many.json
│   │   3_warehouse.json
│   │   4_small_med.json
│   │   5_furniture.json
│   │   6_dense.json
│   │   7_perfect_tile.json
│   │   8_oversized.json
│   └── 9_tall_skinny.json
│
└───vtl_core
    │   utils.py
    │
    ├───domain
    │   └──   models.py
    │
    └───packing
        │   heurisitics.py
        │   processing.py
        └── scoring.py



## API Entrypoint
`api/main.py`
- Exposes endpoints:
  - `GET /health`
  - `POST /pack`

## Data Models
(`api/schemas.py`)
- `Box`
- `Truck`
- `PackingRequest`
- `PlacedBox`
- `PackingResponse`

## Packing Logic
(`vtl_core/packing/processing.py`)
- Receives validated models
- Computes placements
- Returns response model

## Utilities
(`vtl_core/utils.py`)
- Geometry helpers
- Sorting helpers

## Heuristic Scoring Engine

1. Space Utilization = U = Occupied Volume / Total Truck Volume
Range: (0,1)

Goal is to maximize it.

Occupied Volume = sum of all occupied space = sum of all boxes

Total Truck Volume = L * W * H

- The Weight (w_U = 0.5): This is the highest priority. The goal of the project is to fit as much as possible.

2. Structural Stability = S = 1/n * Sum of Area_supported / Area_base

Penalty: Any item with Area_supported < 50% triggers a critical stability warning.

- The Weight (w_S = 0.3): This is 30% of the score. It ensures the items don't fall over.

3. Mass Distribution = M = 1 - |CoG_x,y - Center_x,y| / Max deviation

Goal is to Keep M close to 1.0 to ensure vehicle safety.

- The Weight (w_W = 0.2): This is 20% of the score. It ensures the safety of the truck's axles.

4. C is the number of times a rule was broken, and w_C is the "fine" for that rule.

Rule Violation (C),Penalty Weight (wC​),   Total Deduction
Gravity Violation    0.50                   (0.50⋅count)
Crushing Risk.       0.30                   (0.30⋅count)
Balance Warning      0.20                   (0.20⋅count)

* Total Layout Score (Ls) = (w_U * U) + (w_S * S) + (w_W * M) - (C)

## Optimization & Implementation Strategy

## How To Run
cd python

pip install -r requirements.txt

python api/main.py

## How To Extend
- Add new heuristic → `vtl_core/packing/heuristics.py`
- Include new heuristic among optimization engine selections
- Reconfigure optimization engine calculations to include new heuristic