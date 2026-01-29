import time
from python.vtl_core.schemas import PackingRequest, PackingResponse, PlacedBox

placed = []
unplaced = []

def run_packing(req: PackingRequest) -> PackingResponse:
    start = time.time()

    # TODO: replace with real packing algorithm
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
