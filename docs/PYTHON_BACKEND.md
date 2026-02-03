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
│ ├─ main.py  
│ ├─ routes.py  
│ ├─ logging.py  
│ ├─ config.py  
│ ├─ schemas.py  
│ └─ deps.py    
├─ services/  
│ └─ packing_services.py  
├─ vtl_core/  
│ ├─ __init__.py  
│ ├─ domain/  
│ │ ├─ errors.py  
│ │ └─ models.py  
│ ├─ optimization/  
│ ├─ packing/  
│ │ ├─ constraints.py  
│ │ ├─ heuristics.py  
│ │ ├─ postprocess.py  
│ │ └─ scoring.py  
│ └─ utils.py  
├─ tests/  
│ ├─ test_load.json  
│ ├─ test_optimization.py  
│ └─ test_packing.py  
├─ __init__.py  
└─ requirements.txt  

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
