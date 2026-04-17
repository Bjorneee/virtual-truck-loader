import requests
import json

URL = "http://127.0.0.1:8000/pack"

def run_test():
    payload = {
        "truck": {
            "id": "truck_001",
            "width": 10.0, "height": 10.0, "depth": 10.0,
            "max_weight": 5000.0
        },
        "boxes": [
            {"id": "box_1", "width": 2.0, "height": 2.0, "depth": 2.0, "weight": 10.0},
            {"id": "box_2", "width": 1.0, "height": 1.0, "depth": 1.0, "weight": 5.0}
        ]
    }

    print(f"🚀 Sending request to {URL}...")
    try:
        response = requests.post(URL, json=payload)
        if response.status_code == 200:
            data = response.json()
            print("\n✅ SUCCESS!")
            print(f"Utilization: {data.get('utilization')}")
            print(f"Boxes Placed: {len(data.get('placed', []))}")
            for pb in data.get('placed', []):
                print(f" - {pb['id']} at ({pb['x']}, {pb['y']}, {pb['z']})")
        else:
            print(f"❌ FAILED: {response.text}")
    except Exception as e:
        print(f"🚨 Error: {e}")

if __name__ == "__main__":
    run_test()