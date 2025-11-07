# Unity Client Documentation

## Overview
The Unity client is responsible for:
- User interaction
- Visualizing truck loading results
- Managing local data
- Communicating with the Python backend

## Folder Structure
unity/
└─ Assets/
├─ Scripts/
│ ├─ UI/
│ ├─ Rendering/
│ ├─ Data/
│ └─ Bridge/
├─ Prefabs/
├─ Scenes/
└─ Resources/

## Key Systems

### User Interface
- Menu UI
- Input forms
- Configuration panels

### Python Bridge
- Sends LoadRequest JSON to backend
- Receives LoadResponse
- Handles process startup / health checks

### Renderer
- Displays truck interior
- Places box meshes according to placement data
- Handles camera controls

### Local Database Integration
- Reads/writes warehouse/truck preset data
- SQLite ADO.NET provider

## How To Run
1. Open Unity project
2. Open main scene
3. Press Play
4. Ensure Python backend is running

## How To Add Features
### Add new UI button
1. Create UI element
2. Add C# handler script
3. Connect to bridge/data layer

