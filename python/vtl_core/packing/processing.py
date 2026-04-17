import time
import copy
from typing import List, Tuple, Dict, Any

# API Schemas
from python.api.schemas import PackingRequest, PackingResponse, PlacedBox, Box
# Internal Models
from python.vtl_core.domain.models import Truck_t, Box_t, PlacedBox_t
# Heuristics & Scoring Engine
from python.vtl_core.packing import heurisitics as pack
from python.vtl_core.packing.scoring import ScoringEngine

def create_instances(req: PackingRequest) -> Tuple[Truck_t, List[Box_t]]:
    # Create data model instance of Truck
    truck = Truck_t(
        id=req.truck.id,
        width=req.truck.width,
        height=req.truck.height,
        depth=req.truck.depth,
        max_weight=req.truck.max_weight
    )
    
    # Create list of data model instances of Box
    boxes = [
        Box_t(
            id=box.id, 
            width=box.width, 
            height=box.height, 
            depth=box.depth, 
            weight=box.weight, 
            priority=box.priority
        ) for box in req.boxes
    ]

    return (truck, boxes)

def begin_pack(truck: Truck_t, boxes: List[Box_t]) -> Dict[str, Any]:
    print("\n🔍 Beginning Heuristic Evaluation...")
    start_time = time.time()

    # Save an immutable copy of the original load for fair testing
    original_load = copy.deepcopy(boxes)

    # Initialize the Scoring Engine
    engine = ScoringEngine(truck)

    # Define the available heuristics
    heuristics_pool = {
        "First-Fit Row": pack.ff_row_pack,
        "First-Fit Guillotine": pack.ff_guillotine_pack,
        "MaxRects": pack.maxrects_pack,
        "Skyline": pack.skyline_pack
    }

    best_score = -1.0
    best_payload: Dict[str, Any] = {}
    top_algo = ""
    
    evaluation_results: Dict[str, Any] = {}

    for algo_name, algo_function in heuristics_pool.items():
        print(f"   ▶ Evaluating {algo_name}...")
        
        test_boxes = copy.deepcopy(original_load)
        
        try:
            # Run the algorithm
            result = algo_function(truck=truck, boxes=test_boxes)
            
            # Extract placed boxes and logs (handles both tuple formats)
            placed_internal = result[0] if isinstance(result, tuple) else result
            notes = result[1] if isinstance(result, tuple) and len(result) > 1 else []
            
            # Grade this algorithm's work
            score_data = engine.get_all_scores(placed_internal, original_load)
            current_score = score_data["total_score"]
            
            # Save the full report for this algorithm
            evaluation_results[algo_name] = score_data
            
            # Print the detailed breakdown to the terminal (Out of 100)
            print(f"      ↳ Score: {current_score * 100:.2f} / 100 (Util: {score_data['utilization'] * 100:.2f} / 100, Stab: {score_data['stability'] * 100:.2f} / 100, Mass: {score_data['mass_balance'] * 100:.2f} / 100)")

            # Check if this is the highest score
            if current_score > best_score:
                best_score = current_score
                top_algo = algo_name
                
                # Format the optimal data for the Unity frontend
                placed_schemas = [
                    PlacedBox(id=pb.id, x=pb.x, y=pb.y, z=pb.z, rotation=getattr(pb, 'rotation', 0))
                    for pb in placed_internal
                ]
                placed_ids = {pb.id for pb in placed_internal}
                unplaced_schemas = [
                    Box(id=b.id, width=b.width, height=b.height, depth=b.depth, weight=b.weight, priority=b.priority)
                    for b in original_load if b.id not in placed_ids
                ]

                best_payload = {
                    "placed": placed_schemas,
                    "unplaced": unplaced_schemas,
                    "utilization": current_score, # Keep as float internally for schemas
                    "notes": notes,
                    "metrics": score_data
                }

        except Exception as e:
            print(f"      ↳ ❌ Failed: {e}")
            evaluation_results[algo_name] = {"error": str(e)}

    runtime_ms = (time.time() - start_time) * 1000
    
    # Failsafe in case all algorithms crashed
    if not best_payload:
        print("❌ All heuristics failed. Returning empty payload.")
        return {"placed": [], "unplaced": [Box(**b.__dict__) for b in original_load], "utilization": 0.0, "notes": ["All heuristics failed."], "runtime_ms": runtime_ms}

    best_payload["runtime_ms"] = runtime_ms
    best_payload["evaluation_results"] = evaluation_results 
    
    # Inject the formatted / 100 Performance Report directly into Unity's notes
    best_payload["notes"].append("===================================")
    best_payload["notes"].append("📊 HEURISTIC PERFORMANCE REPORT")
    best_payload["notes"].append("===================================")
    
    for algo, scores in evaluation_results.items():
        if "error" in scores:
            best_payload["notes"].append(f"❌ {algo}: FAILED ({scores['error']})")
        else:
            best_payload["notes"].append(
                f"▶ {algo} -> Total: {scores.get('total_score', 0) * 100:.2f} / 100 | "
                f"Util: {scores.get('utilization', 0) * 100:.2f} / 100 | "
                f"Stab: {scores.get('stability', 0) * 100:.2f} / 100 | "
                f"Mass: {scores.get('mass_balance', 0) * 100:.2f} / 100"
            )

    best_payload["notes"].insert(0, f"⭐ TOP RESULT: {top_algo} with score {best_score * 100:.2f} / 100")

    print(f"✅ Evaluation complete! Top heuristic: {top_algo} in {runtime_ms:.2f}ms\n")
    
    return best_payload