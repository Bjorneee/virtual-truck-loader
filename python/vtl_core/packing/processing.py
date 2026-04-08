from typing import List, Tuple, Optional
from enum import Enum, auto

from python.api.schemas import PackingRequest, PackingResponse, PlacedBox, Box
from python.vtl_core.domain.models import Truck_t, Box_t, PlacedBox_t

from python.vtl_core.packing.heurisitics import first_fit_pack, ff_guillotine_pack

# Enumerations used to select desired layer-packing heuristic
class Hstix(Enum):
    FF  = auto()
    FFG = auto()
    MAX = auto()
    SKY = auto()


def create_instances(req: PackingRequest) -> Tuple[Truck_t, Box_t]:

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
    boxes: Box_t = []
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


def begin_pack(truck: Truck_t, boxes: List[Box_t]) -> Tuple[List[PlacedBox], List[Box], float, List[str]]:

    print("Beginning packing...")

    # Retain original load for future use
    original_load = boxes.copy()
    
    packing_result = layer_pack(
        truck=truck,
        boxes=boxes
    )

    placed: List[PlacedBox] = [PlacedBox.model_validate(p_box) for p_box in packing_result[0]]
    unplaced: List[Box] = [Box.model_validate(box) for box in boxes]
    utilization = get_utilization(truck, packing_result[0], original_load)
    notes: List[str] = packing_result[1]

    print("Packing completed.")

    return (placed, unplaced, utilization, notes)


def layer_pack(truck: Truck_t, boxes: List[Box_t], initial_h: Optional[Hstix] = None) -> Tuple[List[PlacedBox_t], List[str]]:

    z_cursor: float = 0.0
    y_cursor: float = 0.0

    use_heurisitc: Hstix = initial_h
    if not use_heurisitc:
        # Replace with optimization choice
        use_heurisitc = Hstix.FFG

    placed: List[PlacedBox_t] = []
    notes: List[str] = []

    while y_cursor < truck.height and boxes:

        initial_box_count = len(boxes)

        match use_heurisitc:
            case Hstix.FFG:
                print("Packing with FFG")
                layer_data = ff_guillotine_pack(
                    truck=truck,
                    boxes=boxes,
                    layer_y=y_cursor
                )
                print("Layer packed with FFG")
            case _:
                raise ValueError(f"Invalid heuristic choice.")
            
        notes.extend(layer_data[1])

        if not layer_data[0]:
            notes.append("No boxes placed in this iteration")
            break

        placed.extend(layer_data[0])
        y_cursor += layer_data[2]

        if len(boxes) == initial_box_count:
            notes.append("Box list unchanged. Breaking loop.")
            break

        use_heurisitc = Hstix.FFG # Replace with optimization choice
            
    return [placed, notes]



def get_utilization(truck: Truck_t, p_boxes: List[PlacedBox_t], boxes: List[Box_t]) -> float:

    print("Calculating utilization...")

    box_map = {b.id: b for b in boxes}

    total_volume = 0.0
    for p_box in p_boxes:
        matching = box_map.get(p_box.id)
        
        if matching is None:
            raise ValueError(f"Placed Box could not be located in load list\n")
        
        total_volume += matching.volume
    
    return total_volume / truck.volume