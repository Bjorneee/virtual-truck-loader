# System Architecture

## Overview
Provide a high-level description of the Virtual Truck Loader system and what it solves.

## High-Level Diagram
> (Insert architecture diagram here — Unity ⇄ Python ⇄ SQLite)

## Components
- Unity Client
- Python Backend
- SQLite Local DB
- Optional Cloud Services

## Layer Overview
### Unity Frontend
- 3D visualization
- UI for user input
- Python bridge
- Local DB access

### Python Backend
- REST API
- Packing/optimization algorithms
- Geometry + rule validation

### Data Storage
- SQLite local DB
- Optional cloud sync

## Data Flow
1. User configures truck + boxes in Unity.
2. Unity sends JSON to Python (`/load`).
3. Python runs packing algorithm.
4. Python returns placements JSON.
5. Unity renders placements in 3D.
6. (Optional) Data written to DB.

## Technology Choices
- Unity (C#)
- Python (Flask)
- SQLite

## Key Benefits
- Offline-ready
- Cross-platform
- Modular algorithm development

