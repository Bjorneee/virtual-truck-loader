# Python Backend Documentation

## Overview
The Python backend provides:
- A REST API for Unity
- Data validation
- Packing/optimization logic
- Lightweight data processing

## Folder Structure
python/
├─ api/
│ └─ main.py
├─ vtl_core/
│ ├─ schemas.py
│ ├─ packing/
│ │ └─ heuristics.py
│ └─ utils.py
├─ tests/
└─ requirements.txt

## API Entrypoint
`api/main.py`
- Exposes endpoints:
  - `GET /health`
  - `POST /load`

## Data Models
(`vtl_core/schemas.py`)
- `BoxIn`
- `TruckIn`
- `LoadRequest`
- `Placement`
- `LoadResponse`

## Packing Logic
(`vtl_core/packing/heuristics.py`)
- Receives validated models
- Computes placements
- Returns response model

## Utilities
(`vtl_core/utils.py`)
- Geometry helpers
- Sorting helpers

## How To Run
cd python
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python api/main.py

## How To Test
pytest

## How To Extend
- Add new heuristic → `vtl_core/packing/`
- Register new heuristic in API layer
- Update API reference if contract changes
