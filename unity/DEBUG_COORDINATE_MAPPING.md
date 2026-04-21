# Box Placement Debugging Guide

## Where to Find pack_response.json

The file is located in:
```
C:\Users\woxua\AppData\LocalLow\DefaultCompany\unity\pack_response.json
```

This is Unity's `Application.persistentDataPath` for your project.

## JSON Structure

Your API response looks like this:
```json
{
  "placed": [
    {
      "id": "498a8790-9e9a-4b3c-b98a-81cb27353941",
      "x": 0.0,
      "y": 0.0,
      "z": 0.0,
      "rotation": 0
    }
  ],
  "unplaced": [],
  "utilization": 0.08,
  "runtime_ms": 2.66,
  "notes": ["Packed with First-Fit"]
}
```

## Coordinate System Mapping

### Python/API Coordinates (what backend sends):
- **X-axis** = width (2.4m in your truck)
- **Y-axis** = height (2.6m in your truck)
- **Z-axis** = depth/length (6.0m in your truck)
- Origin is at truck **corner (0,0,0)**

### Unity Coordinates (what we use):
- **X-axis** = length/depth (6.0m in your truck) 
- **Y-axis** = height (2.6m in your truck)
- **Z-axis** = width (2.4m in your truck)
- Origin is at truck **center**

### Conversion Formula:
```
Unity X = (API Z - Truck Length / 2) + (Box Length / 2)
Unity Y = (API Y - Truck Height / 2) + (Box Height / 2)
Unity Z = (API X - Truck Width / 2) + (Box Width / 2)
```

## How to Debug

1. Generate a loadout (click "Pack" button)
2. Check the Console for logs that show:
   - `Raw API Response: {...}`
   - `SUCCESS: Placed [ID] at [Unity Position] (api pos: [API Position])`
3. Open the JSON file at the path above and verify coordinates
4. Compare the Unity positions shown in console with where boxes appear visually

## If Boxes Are Still Misplaced

Check:
1. Are box sizes correct? (Length, Width, Height should match what you added)
2. Are the boxes WITHIN these bounds?
   - X: -3.0 to 3.0 (¡ÀTruckL/2)
   - Y: 0 to 2.6 (0 to TruckH)
   - Z: -1.2 to 1.2 (¡ÀTruckW/2)
3. Check the debug logs in Unity Console - they show both API and Unity coordinates
