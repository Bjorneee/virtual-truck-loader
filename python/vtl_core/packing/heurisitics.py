"""
Heuristics for packing algorithms.

Currently implemented heuristics:

- FF-Guillotine (FFG)
- Skyline Sort
- MaxRect

// For Testing
- First Fit Decreasing (FFD)
"""

from typing import List

"""
First-Fit Decreasing bin packing.

Args:
    items: list of item sizes (must be <= bin_capacity)
    bin_capacity: capacity of each bin

Returns:
    A list of bins, each bin is a list of item sizes
"""
def ffd_1d(items: List[float], bin_capacity: float) -> List[List[float]]:

    # Sort items in decreasing order
    items = sorted(items, reverse=True)

    bins: List[List[float]] = []
    remaining_capacity: List[float] = []

    for item in items:
        placed = False

        # Try to place item in the first bin that fits
        for i in range(len(bins)):
            if remaining_capacity[i] >= item:
                bins[i].append(item)
                remaining_capacity[i] -= item
                placed = True
                break

        # If no bin fits, open a new bin
        if not placed:
            bins.append([item])
            remaining_capacity.append(bin_capacity - item)

    return bins
