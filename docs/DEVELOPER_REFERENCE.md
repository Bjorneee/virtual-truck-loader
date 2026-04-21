# Developer Reference

## Dependencies
```powershell
pip install -r dev-requirements.txt
```

## Creating a Test
To create a load for testing:
- Create a .json in python/tests
- Populate with a formatted /pack request
- For formatting, refer to API_REFERENCE.md

## Simulating a Test Case
After creating a test.json in python/tests:

Startup FastAPI server (refer to API_REFERENCE.md)

```powershell
cd {path_to_folder}/virtual-truck-loader

python python/dev_renderer/main.py python/tests/test.json
```

## Modifying Test Environment
(`python/dev_renderer/vconfig.py`)
Can customize:
- Environment Colors
- Box Color Palette
- Grid/Ground Size
- Camera Movement

## Folder Structure

python/
└─ dev_renderer/  
  ├─ main.py  
  ├─ vconfig.py  
  ├─ app/  
  │ ├─ api_client.py  
  │ ├─ loader.py  
  │ └─ viewer.py  
  ├─ camera/  
  │ └─ camera.py  
  ├─ scene/  
  │ ├─ grid.py  
  │ ├─ ground.py  
  │ ├─ lighting.py  
  │ └─ primitives.py  
  └─ utils/  
    ├─ helpers.py  
    └─ json_loader.py  