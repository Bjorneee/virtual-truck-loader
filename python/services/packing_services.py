import time
from typing import List, Tuple

from python.api.schemas import PackingRequest, PackingResponse, PlacedBox, Box
from python.vtl_core.domain import models
from python.vtl_core.packing import heurisitics as packers

from python.vtl_core.utils import get_utilization

def run_packing(req: PackingRequest) -> PackingResponse:
    start = time.time()

    # TODO: replace with real packing algorithm

    # Instantiate truck object
    truck_t: models.Truck_t = models.Truck_t(
        id=req.truck.id,
        width=req.truck.width,
        height=req.truck.height,
        depth=req.truck.depth,
        max_weight=req.truck.max_weight
    )

    # Instantiate all boxes into unplaced list
    unplaced_t: models.Box_t = []
    for box in req.boxes:
        internal = models.Box_t(
            id=box.id,
            width=box.width,
            height=box.height,
            depth=box.depth,
            weight=box.weight,
            priority=box.priority
        )
        unplaced_t.append(Box.model_validate(internal, from_attributes=True))

    # Sort by descending height
    unplaced_t.sort(key=lambda box: box.height, reverse=True)

    pack_result = packers.first_fit_pack(
        truck=truck_t,
        boxes=unplaced_t
    )

    packed_load: PlacedBox = [PlacedBox.model_validate(p_box) for p_box in pack_result[0]]
    unplaced: Box = [Box.model_validate(b) for b in unplaced_t]
    notes: List[str] = pack_result[1]
        
    utilization = 0.0 
    """get_utilization(
        truck=truck,
        load=unplaced,
        placed=packed_load[0]
    )
    """
    runtime_ms = (time.time() - start) * 1000

    return PackingResponse(
        placed=packed_load,
        unplaced=unplaced,
        utilization=utilization,
        runtime_ms=runtime_ms,
        notes=notes
    )
