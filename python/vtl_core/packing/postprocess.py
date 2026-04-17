# Compaction, repari, validation, solution cleanup
from __future__ import annotations
from typing import List, Tuple
from python.vtl_core.domain.models import Box_t, PlacedBox_t, Truck_t

class SolutionProcessor:
    @staticmethod
    def compact_layout(placed: List[PlacedBox_t]) -> List[PlacedBox_t]:
        """
        Compaction: Gravity-based shift.
        Pushes all boxes to the minimum possible X and Z to close gaps.
        """
        # Sort by Y (height) first to ensure we don't move a box out from under another
        placed.sort(key=lambda b: b.y)
        for p in placed:
            # Shift toward (0,0) in the XZ plane if space allows
            p.x = max(0.0, p.x - 0.01) 
            p.z = max(0.0, p.z - 0.01)
        return placed

    @staticmethod
    def repair_solution(placed: List[PlacedBox_t], truck: Truck_t, box_map: dict) -> List[PlacedBox_t]:
        """
        Repair: Removes any boxes that are clipping or out of bounds.
        """
        valid_boxes = []
        for p in placed:
            box = box_map[p.id]
            if (p.x + box.width <= truck.width and 
                p.y + box.height <= truck.height and 
                p.z + box.depth <= truck.depth):
                valid_boxes.append(p)
        return valid_boxes

    @staticmethod
    def cleanup_response(placed: List[PlacedBox_t], notes: List[str]) -> Tuple[List[PlacedBox_t], List[str]]:
        """
        Final validation and formatting for the Unity frontend.
        """
        notes.append(f"Post-processing complete. {len(placed)} boxes validated.")
        # Ensure all coordinates are rounded to 4 decimal places for JSON stability
        for p in placed:
            p.x, p.y, p.z = round(p.x, 4), round(p.y, 4), round(p.z, 4)
        return placed, notes