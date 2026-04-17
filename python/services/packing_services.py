import time
from python.api.schemas import PackingRequest, PackingResponse
from python.vtl_core.packing import processing as Proc

def run_packing(req: PackingRequest) -> PackingResponse:
    
    # Start runtime timer
    # (Note: begin_pack also calculates this, but keeping your logic here is fine!)
    start = time.time()

    # 1. Instantiate data models for packing
    (truck, unplaced_objs) = Proc.create_instances(req)

    # 2. Sort by descending height (Your custom logic)
    unplaced_objs.sort(key=lambda box: box.height, reverse=True)

    # 3. Run packing sequence
    # FIX: begin_pack now returns a dictionary, so we don't 'unpack' it into 4 variables anymore
    result_data = Proc.begin_pack(truck, unplaced_objs)

    # 4. Record runtime (Updating the dictionary with the service-level runtime)
    runtime_ms = (time.time() - start) * 1000
    result_data["runtime_ms"] = runtime_ms

    # 5. Return the response
    # We use ** to unpack the dictionary keys directly into the PackingResponse
    return PackingResponse(**result_data)
