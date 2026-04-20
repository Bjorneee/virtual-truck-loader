import time
import copy
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum, auto

from python.api.schemas import PackingRequest, PlacedBox, Box
from python.vtl_core.domain.models import Truck_t, Box_t, PlacedBox_t, PackRegion

from python.vtl_core.utils import (
    _dims_from_rotation,
    _compute_local_extents,
    _translate_placements
)
from python.vtl_core.packing.heurisitics import (
    ff_row_pack,
    ff_guillotine_pack,
    maxrects_pack,
    skyline_pack,
)
from python.vtl_core.packing.scoring import ScoringEngine

_EPS = 1e-9

class Hstix(Enum):
    FFR = auto()
    FFG = auto()
    MAX = auto()
    SKY = auto()

def create_instances(req: PackingRequest) -> Tuple[Truck_t, List[Box_t]]:
    truck = Truck_t(
        id=req.truck.id,
        width=req.truck.width,
        height=req.truck.height,
        depth=req.truck.depth,
        max_weight=req.truck.max_weight,
    )

    boxes: List[Box_t] = []
    for box in req.boxes:
        boxes.append(
            Box_t(
                id=box.id,
                width=box.width,
                height=box.height,
                depth=box.depth,
                weight=box.weight,
                priority=box.priority,
            )
        )

    return truck, boxes

def get_best_heuristic_for_region(current_truck: Truck_t, current_batch: List[Box_t], region: PackRegion) -> Hstix:
    """
    Simulates packing the current batch in the current region with all available heuristics,
    scores them using the Math Engine, and returns the optimal Hstix enum.
    """
    engine = ScoringEngine(current_truck)
    best_score = -1.0
    best_algo = Hstix.FFG # Default

    heuristics = {
        Hstix.FFR: ff_row_pack,
        Hstix.FFG: ff_guillotine_pack,
        Hstix.MAX: maxrects_pack,
        Hstix.SKY: skyline_pack
    }

    for algo_enum, algo_func in heuristics.items():
        test_truck = copy.deepcopy(current_truck)
        test_batch = copy.deepcopy(current_batch)

        try:
            # 1. Run the simulation
            layer_data = algo_func(truck=test_truck, boxes=test_batch, layer_y=region.y)
            placed_in_batch = layer_data[0]
            
            if not placed_in_batch:
                continue

            # 2. Translate coordinates to absolute truck space for accurate scoring
            _translate_placements(placed_in_batch, region.x, region.z)

            # 3. Score the layout
            score_data = engine.get_all_scores(placed_in_batch, test_batch)
            if score_data["total_score"] > best_score:
                best_score = score_data["total_score"]
                best_algo = algo_enum
        except Exception as e:
            continue

    return best_algo

def begin_pack(truck: Truck_t, boxes: List[Box_t]) -> Dict[str, Any]:
    print(f"\n🔍 Evaluating {len(boxes)} boxes with Regional Dynamic Selection...")
    start_time = time.time()
    original_load = copy.deepcopy(boxes)

    # Execute the core packing loop
    placed_internal, notes = layer_pack(truck=truck, boxes=boxes)

    # Grade the final, completed truck load
    engine = ScoringEngine(truck)
    score_data = engine.get_all_scores(placed_internal, original_load)

    # Format output for the API/Unity
    notes.insert(0, "⭐ REGIONAL DYNAMIC SELECTION ACTIVE")
    notes.append("===================================")
    notes.append(f"📊 FINAL SCORE: {score_data['total_score'] * 100:.2f} / 100")
    notes.append("===================================")

    placed = [PlacedBox(id=pb.id, x=pb.x, y=pb.y, z=pb.z, rotation=getattr(pb, 'rotation', 0)) for pb in placed_internal]
    unplaced = [Box(id=b.id, width=b.width, height=b.height, depth=b.depth, weight=b.weight, priority=b.priority) for b in boxes]

    best_payload = {
        "placed": placed,
        "unplaced": unplaced,
        "utilization": score_data["total_score"],
        "notes": notes,
        "metrics": score_data,
        "runtime_ms": (time.time() - start_time) * 1000
    }
    
    print(f"✅ Dynamic Evaluation complete in {best_payload['runtime_ms']:.2f}ms")
    return best_payload

def layer_pack(
    truck: Truck_t,
    boxes: List[Box_t]
) -> Tuple[List[PlacedBox_t], List[str]]:

    placed: List[PlacedBox_t] = []
    notes: List[str] = []

    # Start with the full original truck as the first region.
    regions: List[PackRegion] = [
        PackRegion(
            x=0.0,
            y=0.0,
            z=0.0,
            width=truck.width,
            depth=truck.depth,
            height=truck.height,
        )
    ]

    layer_index = 0

    while boxes and regions:
        region = regions.pop()

        if region.width <= _EPS or region.depth <= _EPS or region.height <= _EPS:
            continue

        initial_box_count = len(boxes)
        anchor = boxes[0]

        local_truck = Truck_t(
            id=f"{truck.id}_region_{layer_index}",
            width=region.width,
            depth=region.depth,
            height=region.height,
            max_weight=truck.max_weight,
        )

        # --- THE HOOK: Dynamically select the best algorithm for this specific region ---
        heuristic = get_best_heuristic_for_region(local_truck, boxes, region)

        match heuristic:
            case Hstix.FFR:
                layer_data = ff_row_pack(truck=local_truck, boxes=boxes, layer_y=region.y)
                notes.append(f"▶ Region {layer_index}: Selected [First-Fit Row]")
            case Hstix.FFG:
                layer_data = ff_guillotine_pack(truck=local_truck, boxes=boxes, layer_y=region.y)
                notes.append(f"▶ Region {layer_index}: Selected [First-Fit Guillotine]")
            case Hstix.MAX:
                layer_data = maxrects_pack(truck=local_truck, boxes=boxes, layer_y=region.y)
                notes.append(f"▶ Region {layer_index}: Selected [MaxRects]")
            case Hstix.SKY:
                layer_data = skyline_pack(truck=local_truck, boxes=boxes, layer_y=region.y)
                notes.append(f"▶ Region {layer_index}: Selected [Skyline]")
            case _:
                raise ValueError("Invalid heuristic choice.")

        local_placed, layer_notes, used_h, x_cursor, z_cursor = layer_data

        notes.append(
            f"  ↳ origin=({region.x:.3f}, {region.y:.3f}, {region.z:.3f}) "
            f"size=({region.width:.3f}, {region.depth:.3f}, {region.height:.3f})"
        )
        notes.extend(layer_notes)

        # If nothing was placed here, skip this region and continue with the next one.
        if not local_placed:
            notes.append("  ↳ No boxes placed in this region.")
            layer_index += 1
            continue

        # Compute local envelope before translating to absolute truck coordinates.
        used_x, used_z = _compute_local_extents(anchor, local_placed)

        # Translate x/z into absolute coordinates of the original truck.
        _translate_placements(local_placed, region.x, region.z)

        placed.extend(local_placed)

        # ---------- Create child regions ----------

        # 1) Above supported rectangle
        remaining_height_above = region.height - used_h
        if used_h > _EPS and x_cursor > _EPS and z_cursor > _EPS and remaining_height_above > _EPS:
            regions.append(
                PackRegion(
                    x=region.x,
                    y=region.y + used_h,
                    z=region.z,
                    width=x_cursor,
                    depth=z_cursor,
                    height=remaining_height_above,
                )
            )

        # 2) Right floor remainder of the used envelope
        remaining_right_width = region.width - used_x
        if remaining_right_width > _EPS:
            regions.append(
                PackRegion(
                    x=region.x + used_x,
                    y=region.y,
                    z=region.z,
                    width=remaining_right_width,
                    depth=region.depth,
                    height=region.height,
                )
            )

        # 3) Back floor remainder of the used envelope
        remaining_back_depth = region.depth - used_z
        if remaining_back_depth > _EPS and used_x > _EPS:
            regions.append(
                PackRegion(
                    x=region.x,
                    y=region.y,
                    z=region.z + used_z,
                    width=used_x,
                    depth=remaining_back_depth,
                    height=region.height,
                )
            )

        if len(boxes) == initial_box_count:
            notes.append("  ↳ Box list unchanged after placing in region; continuing anyway.")

        layer_index += 1

    return placed, notes

def get_utilization(
    truck: Truck_t,
    p_boxes: List[PlacedBox_t],
    boxes: List[Box_t],
) -> float:
    box_map = {b.id: b for b in boxes}

    total_volume = 0.0
    for p_box in p_boxes:
        matching = box_map.get(p_box.id)
        if matching is None:
            raise ValueError("Placed box could not be located in original load list.")
        total_volume += matching.volume

    return total_volume / truck.volume