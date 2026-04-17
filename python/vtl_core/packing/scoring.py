# Soft-constraint penalties, objective components
from __future__ import annotations
from typing import List, Dict, Any

from python.vtl_core.domain.models import Box_t, PlacedBox_t, Truck_t

class ScoringEngine:
    def __init__(self, truck: Truck_t, weights: Dict[str, float] = None):
        self.truck = truck
        # wU: Utilization, wS: Stability, wM: Mass balance
        self.weights = weights or {"u": 0.5, "s": 0.3, "m": 0.2}

    def get_all_scores(self, placed_boxes: List[PlacedBox_t], original_boxes: List[Box_t]) -> Dict[str, Any]:
        """
        Calculates all metrics independently and returns a dictionary 
        so Unity/Frontend can see exactly why a specific heuristic won.
        """
        if not placed_boxes:
            return {
                "total_score": 0.0,
                "utilization": 0.0,
                "stability": 0.0,
                "mass_balance": 0.0
            }

        box_map = {b.id: b for b in original_boxes}

        # Calculate Individual Metrics
        U = self._calculate_utilization(placed_boxes, box_map)
        S = self._calculate_stability(placed_boxes)
        M = self._calculate_mass_balance(placed_boxes, box_map)

        # Formula: Ls = (wU * U) + (wS * S) + (wM * M)
        total_score = (self.weights['u'] * U) + (self.weights['s'] * S) + (self.weights['m'] * M)
        
        return {
            "total_score": round(total_score, 4),
            "utilization": round(U, 4),
            "stability": round(S, 4),
            "mass_balance": round(M, 4)
        }

    def get_total_score(self, placed_boxes: List[PlacedBox_t], original_boxes: List[Box_t]) -> float:
        """
        Legacy fallback method just in case other files still expect a raw float.
        """
        scores = self.get_all_scores(placed_boxes, original_boxes)
        return scores["total_score"]

    def _calculate_utilization(self, placed_boxes: List[PlacedBox_t], box_map: Dict[str, Box_t]) -> float:
        total_vol = sum(box_map[p.id].width * box_map[p.id].height * box_map[p.id].depth for p in placed_boxes)
        truck_vol = self.truck.width * self.truck.height * self.truck.depth
        return total_vol / truck_vol if truck_vol > 0 else 0.0

    def _calculate_stability(self, placed_boxes: List[PlacedBox_t]) -> float:
        # Note: Switched to p.y == 0 because Unity's vertical axis is Y. 
        # If your internal logic uses Z as vertical, change this back to p.z == 0
        return sum(1.0 if p.y == 0 else 0.8 for p in placed_boxes) / len(placed_boxes)

    def _calculate_mass_balance(self, placed_boxes: List[PlacedBox_t], box_map: Dict[str, Box_t]) -> float:
        mid_x, mid_z = self.truck.width / 2, self.truck.depth / 2
        quads = [0.0, 0.0, 0.0, 0.0] 

        for p in placed_boxes:
            b = box_map[p.id]
            cx, cz = p.x + (b.width / 2), p.z + (b.depth / 2)
            
            # Identify which of the 4 floor quadrants the box center falls into
            idx = (0 if cx < mid_x else 1) + (0 if cz < mid_z else 2)
            quads[idx] += b.weight

        total_mass = sum(quads)
        # 1.0 is perfectly balanced. The larger the gap between heaviest and lightest quadrant, the lower the score.
        return 1.0 - ((max(quads) - min(quads)) / total_mass) if total_mass > 0 else 1.0