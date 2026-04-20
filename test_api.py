import requests

def run_test():
    url = "http://127.0.0.1:8000/pack"
    payload = {
        "truck": {"id": "T-1", "width": 10.0, "height": 10.0, "depth": 10.0, "max_weight": 5000.0},
        "boxes": [
            # FOUR HUGE BASES (Total floor area needed: 144 units. Truck floor: 100 units)
            # This GUARANTEES that at least 2 boxes must be stacked.
            {"id": "Plate-1", "width": 6.0, "height": 2.0, "depth": 6.0, "weight": 500.0, "priority": 1},
            {"id": "Plate-2", "width": 6.0, "height": 2.0, "depth": 6.0, "weight": 500.0, "priority": 1},
            {"id": "Plate-3", "width": 6.0, "height": 2.0, "depth": 6.0, "weight": 500.0, "priority": 1},
            {"id": "Plate-4", "width": 6.0, "height": 2.0, "depth": 6.0, "weight": 500.0, "priority": 1},
            
            # THE TIE-BREAKER: A very thin, heavy item.
            # MaxRects and Skyline handle "slits" in the layout differently than Row-Packers.
            {"id": "Heavy-Sliver", "width": 1.0, "height": 5.0, "depth": 9.0, "weight": 1000.0, "priority": 1}
        ]
    }

    print("🚀 Running the Tetris-Pro Divergence Test...")
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        data = response.json()
        print(f"\n{data['notes'][0]}")
        print("\n--- Performance Report ---")
        for note in data['notes']:
            if "▶" in note: print(f" {note}")
        print(f"\n📦 Items Placed: {len(data['placed'])} / 5")
    else:
        print(f"❌ Error: {response.text}")

if __name__ == "__main__":
    run_test()