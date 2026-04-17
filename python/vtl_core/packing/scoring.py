# Soft-constraint penalties, objective components
from __future__ import annotations
from typing import List, Dict
from python.vtl_core.domain.models import Box_t, PlacedBox_t, Truck_t

class ScoringEngine:
    def __init__(self, truck: Truck_t, weights: Dict[str, float] = None):
        self.truck = truck
        # wU: Utilization, wS: Stability, wM: Mass balance
        self.weights = weights or {"u": 0.5, "s": 0.3, "m": 0.2}

    def get_total_score(self, placed_boxes: List[PlacedBox_t], original_boxes: List[Box_t]) -> float:
        if not placed_boxes:
            return 0.0

        box_map = {b.id: b for b in original_boxes}

        # 1. Utilization (U) - Using same logic as your get_utilization function
        total_vol = sum(box_map[p.id].width * box_map[p.id].height * box_map[p.id].depth for p in placed_boxes)
        U = total_vol / (self.truck.width * self.truck.height * self.truck.depth)

        # 2. Structural Stability (S)
        S = sum(1.0 if p.z == 0 else 0.8 for p in placed_boxes) / len(placed_boxes)

        # 3. Mass Distribution (M) - Using 'weight' from your Box_t
        M = self._calculate_mass_balance(placed_boxes, box_map)

        # Formula: Ls = (wU * U) + (wS * S) + (wM * M)
        ls = (self.weights['u'] * U) + (self.weights['s'] * S) + (self.weights['m'] * M)
        
        return round(ls, 4)

    def _calculate_mass_balance(self, placed_boxes: List[PlacedBox_t], box_map: Dict[str, Box_t]) -> float:
        mid_x, mid_z = self.truck.width / 2, self.truck.depth / 2
        quads = [0.0, 0.0, 0.0, 0.0] 

        for p in placed_boxes:
            b = box_map[p.id]
            cx, cz = p.x + (b.width / 2), p.z + (b.depth / 2)
            idx = (0 if cx < mid_x else 1) + (0 if cz < mid_z else 2)
            quads[idx] += b.weight

        total_mass = sum(quads)
        return 1.0 - ((max(quads) - min(quads)) / total_mass) if total_mass > 0 else 1.0