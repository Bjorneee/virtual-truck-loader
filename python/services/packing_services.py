import time
from python.api.schemas import PackingRequest, PackingResponse, PlacedBox, Box
from python.vtl_core.domain import models

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

    placed = []
    for box in unplaced:
        placed.append(PlacedBox(
            id=box.id,
            x=0.0,
            y=0.0,
            z=0.0,
            rotation=0
        ))
        
    runtime_ms = (time.time() - start) * 1000

    return PackingResponse(
        placed=placed,
        unplaced=unplaced,
        utilization=0.0,
        runtime_ms=runtime_ms,
        notes=["None."]
    )
