from typing import List, Tuple, Dict, Any

from python.api.schemas import PackingRequest, PackingResponse, PlacedBox, Box
from python.vtl_core.domain.models import Truck_t, Box_t, PlacedBox_t
from python.vtl_core.packing import heurisitics as pack


def create_instances(req: PackingRequest) -> Tuple[Truck_t, List[Box_t]]:

    # Create data model instance of Truck
    truck: Truck_t = Truck_t(
        id=req.truck.id,
        width=req.truck.width,
        height=req.truck.height,
        depth=req.truck.depth,
        max_weight=req.truck.max_weight
    )
    print("Truck object instantiated.")

    # Create list of data model instances of Box
    boxes: List[Box_t] = []
    for box in req.boxes:
        internal = Box_t(
            id=box.id,
            width=box.width,
            height=box.height,
            depth=box.depth,
            weight=box.weight,
            priority=box.priority
        )
        boxes.append(internal)
    print("Box objects instantiated.")

    return (truck, boxes)

def begin_pack(truck: Truck_t, boxes: List[Box_t]) -> Dict[str, Any]:

    print("Beginning packing...")

    # Retain original load for future use
    original_load = boxes.copy()

    packing_result = pack.first_fit_pack(
        truck=truck,
        boxes=boxes
    )

    placed: List[PlacedBox] = [PlacedBox.model_validate(p_box) for p_box in packing_result[0]]
    unplaced: List[Box] = [Box.model_validate(box) for box in boxes]
    utilization = get_utilization(truck, packing_result[0], original_load)
    notes: List[str] = packing_result[1]

    print("Packing completed.")

    return {
        "placed": placed,
        "unplaced": unplaced,
        "utilization": utilization,
        "notes": notes
    }


def get_utilization(truck: Truck_t, p_boxes: List[PlacedBox_t], boxes: List[Box_t]) -> float:

    print("Calculating utilization...")

    box_map = {b.id: b for b in boxes}

    total_volume = 0.0
    for p_box in p_boxes:
        matching = box_map.get(p_box.id)
        
        if matching is None:
            raise ValueError(f"Placed Box could not be located in load list\n")
        
        print(matching)
        total_volume += matching.volume
    
    return total_volume / truck.volume