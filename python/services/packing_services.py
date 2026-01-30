import time
from python.vtl_core.schemas import PackingRequest, PackingResponse, PlacedBox
from python.vtl_core.domain import models

def run_packing(req: PackingRequest) -> PackingResponse:
    start = time.time()

    # TODO: replace with real packing algorithm

    # Instantiate truck object
    truck = models.Truck(
        id=req.truck.id,
        width=req.truck.width,
        height=req.truck.height,
        depth=req.truck.depth,
        max_weight=req.truck.max_weight
    )

    # Instantiate all boxes into unplaced list
    unplaced = []
    for box in req.boxes:
        unplaced.append(models.Box(
            id=box.id,
            width=box.width,
            height=box.height,
            depth=box.depth,
            weight=box.weight,
            rotatable=box.rotatable,
            priority=box.priority
        ))

    placed = []
    for box in req.boxes:
        placed.append(PlacedBox(
            id=box.id, 
            x=0.0, 
            y=0.0, 
            z=0.0, 
            rotation=1
            )
        )

    runtime_ms = (time.time() - start) * 1000

    return PackingResponse(
        placed=placed,
        unplaced=unplaced,
        utilization=0.0,
        runtime_ms=runtime_ms,
        notes=["None."]
    )
