import requests
import time
import sys

API_URL = "http://127.0.0.1:8000/pack" 

# Define the test scales: (Total Items, Cubes, Planks, Mixed)
TEST_CASES = [
    (95, 40, 25, 30),
    (250, 100, 75, 75),
    (500, 200, 150, 150),
    (1000, 400, 250, 350),
    (2500, 1000, 750, 750),
    (5000, 2000, 1500, 1500)
]

def run_automated_stress_tests():
    print("🚀 Starting VTL Automated Stress Testing Suite...\n")

    truck = {
        "id": "expo_truck_1",
        "width": 100.0,
        "height": 100.0,
        "depth": 300.0,
        "max_weight": 50000.0
    }

    results = []

    for total, cubes, planks, mixed in TEST_CASES:
        print(f"⏳ Generating payload for {total} items...")
        
        boxes = []
        box_id_counter = 1

        # Batch A: Cubes
        for _ in range(cubes):
            boxes.append({"id": f"cube_{box_id_counter}", "width": 20.0, "height": 20.0, "depth": 20.0, "weight": 15.0, "priority": 1})
            box_id_counter += 1

        # Batch B: Planks
        for _ in range(planks):
            boxes.append({"id": f"plank_{box_id_counter}", "width": 40.0, "height": 10.0, "depth": 50.0, "weight": 35.0, "priority": 1})
            box_id_counter += 1

        # Batch C: Mixed Shapes
        for _ in range(mixed):
            boxes.append({"id": f"mixed_{box_id_counter}", "width": 15.0, "height": 25.0, "depth": 30.0, "weight": 10.0, "priority": 1})
            box_id_counter += 1

        payload = {
            "truck": truck,
            "boxes": boxes
        }

        print(f"📡 Transmitting {total} items to backend. Waiting for KD-Tree to process...")
        
        try:
            start_time = time.time()
            response = requests.post(API_URL, json=payload)
            
            if response.status_code != 200:
                print(f"❌ Server Error {response.status_code} on {total} items: {response.text}")
                continue

            data = response.json()
            latency_ms = (time.time() - start_time) * 1000

            placed_count = len(data.get("placed", []))
            success_rate = (placed_count / total) * 100
            
            metrics = data.get("metrics", {})
            total_score = metrics.get("total_score", 0) * 100
            utilization = metrics.get("utilization", 0) * 100
            stability = metrics.get("stability", 0) * 100
            mass_bal = metrics.get("mass_balance", 0) * 100

            results.append({
                "Total Items": total,
                "Success Rate": f"{success_rate:.1f}% ({placed_count}/{total})",
                "Latency (ms)": f"{latency_ms:.2f} ms",
                "Total Score": f"{total_score:.2f} / 100",
                "Util": f"{utilization:.1f}%",
                "Stab": f"{stability:.1f}%",
                "Mass": f"{mass_bal:.1f}%"
            })
            
            print(f"✅ Success! Latency: {latency_ms:.2f} ms | Score: {total_score:.2f}\n")

        except requests.exceptions.ConnectionError:
            print(f"\n❌ Connection Error: Is your FastAPI server running?")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Unexpected Error on {total} items: {e}")

    # Print Markdown Table for the Report
    print("=========================================================================================")
    print("📊 VTL SCALABILITY BENCHMARKS (COPY INTO REPORT 6)")
    print("=========================================================================================")
    print("| Total Item Count | Placement Success | API Latency (ms) | Algorithmic Score |")
    print("| :--- | :--- | :--- | :--- |")
    for r in results:
        print(f"| {r['Total Items']} Items | {r['Success Rate']} | {r['Latency (ms)']} | {r['Total Score']} |")
    print("=========================================================================================")

if __name__ == "__main__":
    run_automated_stress_tests()