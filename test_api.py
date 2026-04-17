import requests
import json

def run_test():
    url = "http://127.0.0.1:8000/pack"  # Adjust this if your FastAPI endpoint is different

    # The payload formatted to match your Unity API schema
    payload = {
        "truck": {
            "id": "Truck-Alpha",
            "width": 10.0,
            "height": 10.0,
            "depth": 10.0,
            "max_weight": 5000.0
        },
        "boxes": [
            {
                "id": "Container-1-Base",
                "width": 5.0,
                "height": 3.0,
                "depth": 5.0,
                "weight": 200.0,
                "priority": 1
            },
            {
                "id": "Container-2-Base",
                "width": 5.0,
                "height": 3.0,
                "depth": 5.0,
                "weight": 200.0,
                "priority": 1
            },
            {
                "id": "Container-3-HeavyBeam",
                "width": 2.0,
                "height": 2.0,
                "depth": 8.0,
                "weight": 500.0,  
                "priority": 1
            },
            {
                "id": "Container-4-LightBox",
                "width": 2.0,
                "height": 2.0,
                "depth": 2.0,
                "weight": 15.0,   
                "priority": 1
            },
            {
                "id": "Container-5-FlatRoof",
                "width": 8.0,
                "height": 1.0,
                "depth": 8.0,
                "weight": 50.0,
                "priority": 1
            }
        ]
    }

    print("🚀 Sending 5-Container payload to Virtual Truck Loader API...")
    
    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            
            print("\n✅ SUCCESS! Received response from server.\n")
            
            # 1. Print the Winning Results
            print("=" * 40)
            print("⭐ OPTIMAL HEURISTIC SELECTED")
            print("=" * 40)
            print(f"Utilization Score:  {data.get('utilization', 0) * 100:.2f} / 100")
            print(f"Runtime:            {data.get('runtime_ms', 0):.2f} ms")
            
            # Print notes to see the optimal algorithm announcement and the new performance report
            for note in data.get("notes", []):
                print(f" - {note}")

            # 2. Print Coordinates of Placed Boxes
            print("\n📦 PLACED BOX COORDINATES:")
            for pb in data.get("placed", []):
                print(f" [{pb['id']}] -> x: {pb['x']}, y: {pb['y']}, z: {pb['z']}, rot: {pb.get('rotation', 0)}")
                
            unplaced = data.get("unplaced", [])
            if unplaced:
                print(f"\n❌ UNPLACED BOXES: {len(unplaced)}")
                for ub in unplaced:
                    print(f" - {ub['id']}")
                    
            print("\n")

        else:
            print(f"❌ Server Error {response.status_code}: {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to the server. Is FastAPI running?")

if __name__ == "__main__":
    run_test()