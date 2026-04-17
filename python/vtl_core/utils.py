# geometry helpers, bin fit checks

from typing import List, Tuple

from python.vtl_core.domain import models

def get_utilization(
        truck: models.Truck_t, 
        load: List[models.Box_t], 
        placed: List[models.PlacedBox_t]
    ) -> float :
    
    total_volume : float = 0;
    for p_box in placed:
        current = next((box for box in load if box.id == p_box.id), None)

        if current:
            total_volume += current.volume()
        else:
            raise ValueError(f"Placed box could not be located in load list.\n")

    return total_volume / truck.volume()