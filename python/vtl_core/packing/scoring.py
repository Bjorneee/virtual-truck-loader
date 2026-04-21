from __future__ import annotations
from typing import List, Dict, Any
from python.vtl_core.domain.models import Box_t, PlacedBox_t, Truck_t

class ScoringEngine:
    def __init__(self, truck: Truck_t, weights: Dict[str, float] = None):
        self.truck = truck
        # Weights: 50% Space, 30% Stability, 20% Weight Balance
        self.weights = weights or {"u": 0.5, "s": 0.3, "m": 0.2}

    def get_all_scores(self, placed_boxes: List[PlacedBox_t], original_boxes: List[Box_t]) -> Dict[str, Any]:
        if not placed_boxes:
            return {"total_score": 0.0, "utilization": 0.0, "stability": 0.0, "mass_balance": 0.0}

        box_map = {b.id: b for b in original_boxes}
        U = self._calculate_utilization(placed_boxes, box_map)
        S = self._calculate_stability(placed_boxes)
        M = self._calculate_mass_balance(placed_boxes, box_map)

        total_score = (self.weights['u'] * U) + (self.weights['s'] * S) + (self.weights['m'] * M)
        
        return {
            "total_score": round(total_score, 4),
            "utilization": round(U, 4),
            "stability": round(S, 4),
            "mass_balance": round(M, 4)
        }

    def _calculate_utilization(self, placed_boxes: List[PlacedBox_t], box_map: Dict[str, Box_t]) -> float:
        total_vol = sum(box_map[p.id].width * box_map[p.id].height * box_map[p.id].depth for p in placed_boxes)
        truck_vol = self.truck.width * self.truck.height * self.truck.depth
        return total_vol / truck_vol if truck_vol > 0 else 0.0

    def _calculate_stability(self, placed_boxes: List[PlacedBox_t]) -> float:
        # Unity uses Y for height
        return sum(1.0 if p.y == 0 else 0.8 for p in placed_boxes) / len(placed_boxes)

    def _calculate_mass_balance(self, placed_boxes: List[PlacedBox_t], box_map: Dict[str, Box_t]) -> float:
        mid_x, mid_z = self.truck.width / 2, self.truck.depth / 2
        quads = [0.0, 0.0, 0.0, 0.0] 
        for p in placed_boxes:
            b = box_map[p.id]
            # Center-based quadrant detection
            idx = (0 if (p.x + b.width/2) < mid_x else 1) + (0 if (p.z + b.depth/2) < mid_z else 2)
            quads[idx] += b.weight
        total_mass = sum(quads)
        return 1.0 - ((max(quads) - min(quads)) / total_mass) if total_mass > 0 else 1.0