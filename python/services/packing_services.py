import time
from typing import List, Tuple
from python.api.schemas import PackingRequest, PackingResponse, PlacedBox, Box
from python.vtl_core.domain import models
from python.vtl_core.packing import heurisitics as packers

def run_packing(req: PackingRequest) -> PackingResponse:
    start = time.time()

    # TODO: replace with real packing algorithm

    # Instantiate truck object
    truck = models.Truck_t(
        id=req.truck.id,
        width=req.truck.width,
        height=req.truck.height,
        depth=req.truck.depth,
        max_weight=req.truck.max_weight
    )

    # Instantiate all boxes into unplaced list
    unplaced = []
    for box in req.boxes:
        internal = models.Box_t(
            id=box.id,
            width=box.width,
            height=box.height,
            depth=box.depth,
            weight=box.weight,
            priority=box.priority
        )
        unplaced.append(Box.model_validate(internal, from_attributes=True))

    # Sort by descending height
    unplaced.sort(key=lambda box: box.height, reverse=True)

    # Run packing algorithm (ff guillotine for current implementation)
    """
    *Note: Current ffg implementation does not place boxes with id. Instead, it attempts
    to match each placed box to an existing id. Need to change this eventually, as it will
    likely cause problems for boxes with matching specs.
    """
    packed_load = packers.pack_truck_ff_guillotine_top_left(
        truck=truck,
        boxes=unplaced
    )
        
    runtime_ms = (time.time() - start) * 1000

    return PackingResponse(
        placed=packed_load[0],
        unplaced=packed_load[1],
        utilization=0.0,
        runtime_ms=runtime_ms,
        notes=["None."]
    )
