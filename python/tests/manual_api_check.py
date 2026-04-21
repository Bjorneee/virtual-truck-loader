import requests

def run_multi_size_test():
    url = "http://127.0.0.1:8000/pack"
    
    # A standard 10x10x10 truck
    payload = {
        "truck": {
            "id": "Demo-Truck", 
            "width": 10.0, 
            "height": 10.0, 
            "depth": 10.0, 
            "max_weight": 5000.0
        },
        "boxes": [
            # 1. Large Base Pallets (Creates initial floor platforms)
            {"id": "Pallet-A", "width": 6.0, "height": 2.0, "depth": 6.0, "weight": 400.0, "priority": 1},
            {"id": "Pallet-B", "width": 4.0, "height": 2.0, "depth": 6.0, "weight": 300.0, "priority": 1},
            
            # 2. Long Awkward Beams (Tests +x or +z remaining space)
            {"id": "Long-Beam-1", "width": 8.0, "height": 1.0, "depth": 2.0, "weight": 150.0, "priority": 1},
            {"id": "Long-Beam-2", "width": 2.0, "height": 1.0, "depth": 8.0, "weight": 150.0, "priority": 1},
            
            # 3. Tall Pillars (Tests +y 'Above' regions and stability)
            {"id": "Pillar-1", "width": 2.0, "height": 6.0, "depth": 2.0, "weight": 100.0, "priority": 1},
            {"id": "Pillar-2", "width": 2.0, "height": 6.0, "depth": 2.0, "weight": 100.0, "priority": 1},
            
            # 4. Small Heavy Cubes (Tests tight gaps and mass balance)
            {"id": "Dense-Cube-1", "width": 2.0, "height": 2.0, "depth": 2.0, "weight": 500.0, "priority": 1},
            {"id": "Dense-Cube-2", "width": 2.0, "height": 2.0, "depth": 2.0, "weight": 500.0, "priority": 1},
            
            # 5. Flat Roof Panels (Tests the absolute top of the truck)
            {"id": "Roof-Panel", "width": 5.0, "height": 0.5, "depth": 5.0, "weight": 50.0, "priority": 1}
        ]
    }

    print("🚀 Running Multi-Size Dynamic Selection Test...")
    
    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            
            print("\n===================================")
            print("📦 PACKING SUMMARY")
            print("===================================")
            print(f"Items Placed:   {len(data['placed'])} / {len(payload['boxes'])}")
            print(f"Items Unplaced: {len(data['unplaced'])}")
            print(f"Runtime:        {data.get('runtime_ms', 0):.2f} ms")
            
            print("\n===================================")
            print("🧠 DYNAMIC ENGINE NOTES")
            print("===================================")
            for note in data.get('notes', []):
                # Highlight the algorithm selections
                if "Selected" in note or "FINAL SCORE" in note or "REGION" in note.upper():
                    print(note)
                elif "origin=" in note: # Print coordinates for debugging
                    print(note)
                    
        else:
            print(f"❌ Server Error {response.status_code}: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Is your FastAPI server running on port 8000?")

if __name__ == "__main__":
    run_multi_size_test()