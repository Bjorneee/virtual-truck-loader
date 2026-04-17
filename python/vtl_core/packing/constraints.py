# bounds, weight, stacking rules
from __future__ import annotations
from typing import List
from python.vtl_core.domain.models import Box_t, PlacedBox_t, Truck_t

class PhysicalConstraints:
    def __init__(self, truck: Truck_t):
        self.truck = truck

    def validate_bounds(self, p_box: PlacedBox_t, box_data: Box_t) -> bool:
        """Checks if the box exceeds truck dimensions."""
        within_x = 0 <= p_box.x and (p_box.x + box_data.width) <= self.truck.width
        within_y = 0 <= p_box.y and (p_box.y + box_data.height) <= self.truck.height
        within_z = 0 <= p_box.z and (p_box.z + box_data.depth) <= self.truck.depth
        return within_x and within_y and within_z

    def validate_weight_limit(self, placed_boxes: List[PlacedBox_t], box_map: dict) -> bool:
        """Checks if total weight exceeds truck.max_weight."""
        current_weight = sum(box_map[p.id].weight for p in placed_boxes)
        return current_weight <= self.truck.max_weight

    def validate_stacking(self, p_box: PlacedBox_t, all_placed: List[PlacedBox_t], box_map: dict) -> bool:
        """Ensures the box is not floating and follows basic stacking rules."""
        if p_box.y == 0:  # On the floor
            return True
        
        # Check if any box is directly underneath this one (Y-axis is height)
        for other in all_placed:
            if other.id == p_box.id: continue
            other_data = box_map[other.id]
            
            # Check if 'other' is below 'p_box' and they overlap in X/Z plane
            is_below = (other.y + other_data.height) <= p_box.y
            x_overlap = p_box.x < (other.x + other_data.width) and (p_box.x + box_map[p_box.id].width) > other.x
            z_overlap = p_box.z < (other.z + other_data.depth) and (p_box.z + box_map[p_box.id].depth) > other.z
            
            if is_below and x_overlap and z_overlap:
                return True
        return False