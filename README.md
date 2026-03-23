# virtual-truck-loader
Virtual truck loading application. Made for SJSU CMPE195 F25-S26 Senior Project.

## Team
- Benicio Marenco (Bjorneee)
- Anh Khoi Pham (kphamcodes/AsnNightOwl)
- Jingkai Yao (d4clovetrain)
- Anson Lee (anxonlee)

## Prerequisites
- Unity version 6000.3.11f1 and a Unity account
- Visual Studio Code/Visual Studio Community
- Python Extensions:
  - fastapi         # Serves HTTP API to Unity
  - uvicorn
  - python-dotenv
  - pydantic>=2     # Data validation & schemas for request/response
  - pydantic-settings
  
  - numpy           # Core math / geometry operations
  
  - pandas          # Data manipulation for tabular data
  - scipy           # Optimization helpers
  - ortools         # Advanced bin packing / optimization & constraint solving


## Installation
- Download Unity and the correct editor version
- Click on the green code button
- Copy URL to clone repo (or choose your preferred cloning method)
- Open VS Code in your preferred directory and open the terminal
- Paste [git clone https://github.com/Bjorneee/virtual-truck-loader.git]
- Open Unity project
- Open Visual Studio code and navigate to the preferred branch
- Project should be loaded onto Unity for use

## Configuration
- Unity Configuration
  - Install Unity Editor version 6000.3.11f1
  - Open the unity/ folder as a Unity project
  - No API keys or environment variables are currently required for Unity itself
- Python Backend Configuration
  - Install required Python dependencies:
  - fastapi, uvicorn, pydantic
  - numpy, pandas, scipy, ortools (for packing algorithm)
  - python-dotenv, pydantic-settings

## Running the Application
- Press play button on the top middle of the Unity editor

## Usage
- Input Truck Dimensions and Package Properties using the groups of text boxes
- The top navigation bar contains a series of function buttons
  - Save Button Saves data and position of current boxes in the scene
  - File Button currently Resets the scene
  - Add Button adds a box with randomized dimensions
  - Load Button Loads the previous saved instance
  - View Button rotates between different view angles of the scene\
  - Settings button allows the user to switch between algorithm settings and adjust the sorting time.
- Generate Loadout Button on the bottom of the screen runs the packing algorithm and loads the sorted layout on the scene.


## Project Structure
virtual-truck-loader/
│
├── unity/        # Unity frontend (3D UI, interaction, visualization)
├── python/       # FastAPI backend (packing algorithm + API endpoints)
├── database/     # Likely data storage / schemas (not heavily used yet)
├── docs/         # Documentation (API reference, design notes)\
├── tools/        # Utility scripts / helpers
├── README.md

Key Folders Explained
unity/
Main frontend application
Handles:
UI (buttons like Add, Save, Load, Pack)
3D box visualization
user interaction (drag/drop, camera views)
Written in C# (Unity scripts)

python/
  Backend API using FastAPI
  Handles:
    /health endpoint (status check)
    /pack endpoint (core packing algorithm)
  Uses:
    OR-Tools / SciPy for optimization
    Pydantic for request/response validation

database/
  Placeholder or future storage layer
  Likely intended for:
    saved layouts
    inventory data
    persistent configurations

docs/
  Contains documentation like:
    API reference (/pack, /health)
    usage instructions
    Useful for frontend/backend integration

tools/
  Utility scripts or helper programs
  May include:
    test data
    automation scripts
