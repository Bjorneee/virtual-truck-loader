import time

from python.api.schemas import PackingRequest, PackingResponse
from python.vtl_core.packing import processing as Proc

def run_packing(req: PackingRequest) -> PackingResponse:
    
    # Start runtime timer
    start = time.time()

    # Instantiate data models for packing
    (truck, unplaced_objs) = Proc.create_instances(req)

    # Sort by descending height
    unplaced_objs.sort(key=lambda box: box.height, reverse=True)

    # Run packing sequence
    pack_result = Proc.begin_pack(truck, unplaced_objs)

    # Record runtime
    pack_result["runtime_ms"] = (time.time() - start) * 1000
    return PackingResponse(**pack_result)
