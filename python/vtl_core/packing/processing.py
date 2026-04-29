import time
import copy
from typing import List, Tuple, Dict, Any
from enum import Enum, auto

from python.api.schemas import PackingRequest, PlacedBox, Box
from python.vtl_core.domain.models import Truck_t, Box_t, PlacedBox_t, PackRegion

from python.vtl_core.utils import (
    _compute_local_extents,
    _translate_placements
)
from python.vtl_core.packing.heurisitics import (
    ff_row_pack,
    ff_guillotine_pack,
    maxrects_pack,
    skyline_pack,
)

_EPS = 1e-9

class Hstix(Enum):
    FFR = auto()
    FFG = auto()
    MAX = auto()
    SKY = auto()

# ==========================================
# 🧠 DYNAMIC SCORING ENGINE (Physics Based)
# ==========================================
class ScoringEngine:
    def __init__(self, truck: Truck_t):
        self.truck = truck

    def _get_dims(self, p_box: PlacedBox_t, box_map: dict) -> Tuple[float, float, float, float]:
        """Helper to safely retrieve dimensions and weight, accounting for rotation."""
        orig = box_map.get(p_box.id)
        if not orig:
            return 0.0, 0.0, 0.0, 1.0

        w, h, d = orig.width, orig.height, orig.depth
        wt = getattr(orig, 'weight', 1.0)

        # Swap width and depth if the box was rotated 90/270 degrees on the Y axis
        rot = getattr(p_box, 'rotation', 0)
        if rot == 1 or rot == 3:
            w, d = d, w
            
        return w, h, d, wt

    def get_all_scores(self, placed_boxes: List[PlacedBox_t], original_batch: List[Box_t]) -> Dict[str, float]:
        """Calculates the weighted tournament score for a layout."""
        if not placed_boxes:
            return {"utilization": 0.0, "stability": 0.0, "mass_balance": 0.0, "total_score": 0.0}

        # Create lookup map for dimensions/weights
        box_map = {b.id: b for b in original_batch}

        # Calculate metrics using the map
        util_score = self._calc_utilization(placed_boxes, box_map)
        stability_score = self._calc_stability(placed_boxes, box_map)
        mass_score = self._calc_mass_balance(placed_boxes, box_map)

        # Weighted Total (Matches the Slide Deck Formula)
        total_score = (0.60 * util_score) + (0.30 * stability_score) + (0.10 * mass_score)

        return {
            "utilization": util_score,
            "stability": stability_score,
            "mass_balance": mass_score,
            "total_score": total_score
        }

    def _calc_utilization(self, placed_boxes: List[PlacedBox_t], box_map: dict) -> float:
        truck_vol = self.truck.width * self.truck.height * self.truck.depth
        used_vol = 0.0
        for b in placed_boxes:
            w, h, d, _ = self._get_dims(b, box_map)
            used_vol += (w * h * d)
        return used_vol / truck_vol if truck_vol > 0 else 0.0

    def _calc_stability(self, placed_boxes: List[PlacedBox_t], box_map: dict) -> float:
        if not placed_boxes: 
            return 0.0
            
        total_stability = 0.0

        for box in placed_boxes:
            b_w, b_h, b_d, _ = self._get_dims(box, box_map)
            base_area = b_w * b_d
            
            # 100% supported if on the truck floor
            if abs(box.y) < 1e-9:
                total_stability += 1.0 
                continue

            supported_area = 0.0
            for under in placed_boxes:
                u_w, u_h, u_d, _ = self._get_dims(under, box_map)
                
                # Check if 'under' box is directly below 'box'
                if abs((under.y + u_h) - box.y) < 0.001:
                    # Calculate overlapping area on the X-Z plane
                    overlap_x = max(0, min(box.x + b_w, under.x + u_w) - max(box.x, under.x))
                    overlap_z = max(0, min(box.z + b_d, under.z + u_d) - max(box.z, under.z))
                    supported_area += (overlap_x * overlap_z)

            # Ratio of supported area to total base area
            stability_ratio = min(1.0, supported_area / base_area) if base_area > 0 else 0
            total_stability += stability_ratio

        # Return average stability across all boxes
        return total_stability / len(placed_boxes)

    def _calc_mass_balance(self, placed_boxes: List[PlacedBox_t], box_map: dict) -> float:
        if not placed_boxes: 
            return 0.0

        total_weight = sum(self._get_dims(b, box_map)[3] for b in placed_boxes)
        if total_weight == 0: 
            return 1.0

        cog_x, cog_z = 0.0, 0.0
        
        # Calculate actual Center of Gravity (X and Z coordinates)
        for b in placed_boxes:
            b_w, _, b_d, b_wt = self._get_dims(b, box_map)
            cog_x += (b.x + b_w / 2) * b_wt
            cog_z += (b.z + b_d / 2) * b_wt
            
        cog_x /= total_weight
        cog_z /= total_weight

        # Ideal Center of Gravity is the exact center of the truck floor
        ideal_x = self.truck.width / 2
        ideal_z = self.truck.depth / 2

        # Calculate deviation
        deviation_x = abs(cog_x - ideal_x)
        deviation_z = abs(cog_z - ideal_z)

        # Normalize the deviation (1.0 = perfectly centered, 0.0 = entirely on the edge)
        max_dev_x = self.truck.width / 2
        max_dev_z = self.truck.depth / 2

        score_x = 1.0 - (deviation_x / max_dev_x) if max_dev_x > 0 else 1.0
        score_z = 1.0 - (deviation_z / max_dev_z) if max_dev_z > 0 else 1.0

        return (score_x + score_z) / 2


# ==========================================
# 📦 CORE PACKING LOGIC
# ==========================================
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
            layer_data = algo_func(truck=test_truck, boxes=test_batch, layer_y=region.y)
            placed_in_batch = layer_data[0]
            
            if not placed_in_batch:
                continue

            _translate_placements(placed_in_batch, region.x, region.z)

            score_data = engine.get_all_scores(placed_in_batch, test_batch)
            current_score = score_data["total_score"]

            if current_score > best_score:
                best_score = current_score
                best_algo = algo_enum
        except Exception:
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
    notes.append(f"   ↳ Utilization: {score_data['utilization'] * 100:.1f}%")
    notes.append(f"   ↳ Stability:   {score_data['stability'] * 100:.1f}%")
    notes.append(f"   ↳ Mass Bal:    {score_data['mass_balance'] * 100:.1f}%")
    notes.append("===================================")

    # Convert internal models back to API models
    placed = [PlacedBox(id=pb.id, x=pb.x, y=pb.y, z=pb.z, rotation=getattr(pb, 'rotation', 0)) for pb in placed_internal]
    unplaced = [Box(id=b.id, width=b.width, height=b.height, depth=b.depth, weight=b.weight, priority=b.priority) for b in boxes]

    # Return exactly the Dictionary payload the FastAPI router expects
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

        if not local_placed:
            notes.append("  ↳ No boxes placed in this region.")
            layer_index += 1
            continue

        used_x, used_z = _compute_local_extents(anchor, local_placed)
        _translate_placements(local_placed, region.x, region.z)

        placed.extend(local_placed)

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

        # 2) Right floor remainder
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

        # 3) Back floor remainder
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