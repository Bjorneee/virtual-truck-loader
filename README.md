# virtual-truck-loader
Virtual truck loading application. Made for SJSU CMPE195 F25-S26 Senior Project.

## Team
- Benicio Marenco (Bjorneee)
- Anh Khoi Pham (kphamcodes/AsnNightOwl)
- Jingkai Yao (d4clovetrain)
- Anson Lee (anxonlee)

## User Installation (Windows Only)
- Select 'VTL Prototype Build' under Releases in the rop right corner
- select 'VTL.zip' to download the compressed application file
- Locate the zip file in your file explorer and extract it to your desired location
- open the 'backend' folder and run 'backend.exe' (This starts up the backend server, will patch soon to only require VTL.exe to start up to start server)
- run 'VTL.exe' to start the application

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

## Developer Prerequisites
- Unity version 6000.3.11f1 and a Unity account
- Visual Studio Code/Visual Studio Community
- Python Extensions:
  - fastapi         # Serves HTTP API to Unity
  - uvicorn
  - python-dotenv
  - pydantic>=2     # Data validation & schemas for request/response
  - pydantic-settings
 
### Currently Unused Packages
  - numpy           # Core math / geometry operations
  - pandas          # Data manipulation for tabular data
  - scipy           # Optimization helpers
  - ortools         # Advanced bin packing / optimization & constraint solving

## Configuration
- Unity Configuration
  - Install Unity Editor version 6000.3.11f1
  - Open the unity/ folder as a Unity project
  - No API keys or environment variables are currently required for Unity itself
- Python Backend Configuration
  - Install required Python dependencies:
  - fastapi, uvicorn, pydantic

## Testing the Application
- Press play button on the top middle of the Unity editor

## Project Structure
virtual-truck-loader/  
├── unity/        # Unity frontend (3D UI, interaction, visualization)  
├── python/       # FastAPI backend (packing algorithm + API endpoints)  
├── docs/         # Documentation (API reference, design notes)\  
├── tests/        # Automated CI/CD pipeline scripts + test load jsons 
├── README.md  

unity/
  - Main frontend application
  - Handles:
    - UI (buttons like Add, Save, Load, Pack)
    - 3D box visualization
    - user interaction (drag/drop, camera views)
    - Written in C# (Unity scripts)

python/
  - Backend API using FastAPI
  - Handles:
    - /health endpoint (status check)
    - /pack endpoint (core packing algorithm)
    - Heuristic layer/region packing
    - Heuristic optimization

docs/
  - Contains documentation like:
    - API reference (/pack, /health)
    - Usage instructions

tests/
  - Contains python test scripts for:
    - Unit Tests
    - Integration Tests
    - E2E Tests
    - Edge Case Tests
    - Stress Test

## Coverage
![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)