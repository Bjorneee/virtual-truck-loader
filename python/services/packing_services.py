import time
from python.api.schemas import PackingRequest, PackingResponse, PlacedBox

def run_packing(req: PackingRequest) -> PackingResponse:
    start = time.time()

    # TODO: replace with real packing algorithm
    placed = []
    unplaced = []

    for box in req.boxes:
        unplaced.append(box.id)

    runtime_ms = (time.time() - start) * 1000

    return PackingResponse(
        placed=placed,
        unplaced=unplaced,
        utilization=0.0,
        runtime_ms=runtime_ms,
    )
