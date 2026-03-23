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

## Configuration


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
