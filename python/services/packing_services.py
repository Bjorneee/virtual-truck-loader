import time

from python.api.schemas import PackingRequest, PackingResponse
from python.vtl_core.packing import processing as Proc

def run_packing(req: PackingRequest) -> PackingResponse:
    
    # Start runtime timer
    start = time.time()

    # Instantiate data models for packing
    (truck, unplaced) = Proc.create_instances(req)

    # Sort by descending height
    unplaced.sort(key=lambda box: box.height, reverse=True)

    # Run packing sequence
    (placed, unplaced, utilization, notes) = Proc.begin_pack(truck, unplaced)

    # Record runtime
    runtime_ms = (time.time() - start) * 1000
    return PackingResponse(
        placed=placed,
        unplaced=unplaced,
        utilization=utilization,
        runtime_ms=runtime_ms,
        notes= notes
    )
