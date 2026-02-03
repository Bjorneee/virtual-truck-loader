"""
Heuristics for packing algorithms.

Currently implemented heuristics:

- FF-Guillotine (FFG)
- Skyline Sort
- MaxRect

// For Testing
- First Fit Decreasing (FFD)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from python.vtl_core.domain.models import Box_t, PlacedBox_t, Truck_t

"""

First-Fit Guillotine (FFG)

"""

# ----------------------------
# Geometry helpers (top-right origin)
# ----------------------------
# Coordinate system for each 2D layer (width x depth):
#   origin (0,0) is TOP-RIGHT corner of the layer rectangle
#   x increases LEFTWARD  (toward -X in conventional space)
#   y increases DOWNWARD  (toward +Z or +Y depending on your Unity mapping)
#
# A free-rectangle is represented by its top-right corner (xr, yt) and size (w,h),
# where it spans:
#   x in [xr - w, xr]
#   y in [yt, yt + h]


@dataclass(frozen=True)
class Rect2D:
    w: float  # width (layer-x extent)
    h: float  # height (layer-y extent), here "depth"


@dataclass
class FreeRectTR:
    xr: float  # x coordinate of top-right corner
    yt: float  # y coordinate of top-right corner
    w: float
    h: float

    @property
    def xl(self) -> float:
        return self.xr - self.w

    @property
    def yb(self) -> float:
        return self.yt + self.h


def _contains(a: FreeRectTR, b: FreeRectTR) -> bool:
    # a contains b (in TR coordinate space)
    return (a.xl <= b.xl) and (a.xr >= b.xr) and (a.yt <= b.yt) and (a.yb >= b.yb)


def _almost_eq(a: float, b: float, eps: float = 1e-9) -> bool:
    return abs(a - b) <= eps


def _prune_contained(free_rects: List[FreeRectTR]) -> List[FreeRectTR]:
    out: List[FreeRectTR] = []
    for i, r in enumerate(free_rects):
        contained = False
        for j, s in enumerate(free_rects):
            if i != j and _contains(s, r):
                contained = True
                break
        if not contained:
            out.append(r)

    # remove exact duplicates
    uniq: List[FreeRectTR] = []
    seen = set()
    for r in out:
        key = (r.xr, r.yt, r.w, r.h)
        if key not in seen:
            seen.add(key)
            uniq.append(r)
    return uniq


def _merge_guillotine(free_rects: List[FreeRectTR]) -> List[FreeRectTR]:
    """
    Optional merge step:
      - merge horizontally adjacent rects with same (yt,h) and touching in x
      - merge vertically adjacent rects with same (xr,w) and touching in y

    Because we use TR corners, adjacency checks are careful about edges.
    """
    changed = True
    rects = free_rects[:]

    while changed:
        changed = False
        rects = _prune_contained(rects)

        # Horizontal merges (side-by-side along x)
        rects.sort(key=lambda r: (r.yt, r.h, r.xr, r.w))
        i = 0
        while i < len(rects):
            a = rects[i]
            merged = False
            for j in range(i + 1, len(rects)):
                b = rects[j]
                if not (_almost_eq(a.yt, b.yt) and _almost_eq(a.h, b.h)):
                    continue

                # a and b share same vertical span; check if they touch along x
                # If b is immediately to the left of a:
                #   b.xr == a.xl
                if _almost_eq(b.xr, a.xl):
                    # merged rect top-right is a.xr, width = a.w + b.w
                    rects.pop(j)
                    rects.pop(i)
                    rects.append(FreeRectTR(xr=a.xr, yt=a.yt, w=a.w + b.w, h=a.h))
                    changed = True
                    merged = True
                    break

                # If a is immediately to the left of b:
                if _almost_eq(a.xr, b.xl):
                    rects.pop(j)
                    rects.pop(i)
                    rects.append(FreeRectTR(xr=b.xr, yt=b.yt, w=a.w + b.w, h=a.h))
                    changed = True
                    merged = True
                    break

            if not merged:
                i += 1

        if changed:
            continue

        # Vertical merges (stacked along y)
        rects.sort(key=lambda r: (r.xr, r.w, r.yt, r.h))
        i = 0
        while i < len(rects):
            a = rects[i]
            merged = False
            for j in range(i + 1, len(rects)):
                b = rects[j]
                if not (_almost_eq(a.xr, b.xr) and _almost_eq(a.w, b.w)):
                    continue

                # They share same horizontal span; check if they touch along y
                # If b is immediately below a:
                #   b.yt == a.yb
                if _almost_eq(b.yt, a.yb):
                    rects.pop(j)
                    rects.pop(i)
                    rects.append(FreeRectTR(xr=a.xr, yt=a.yt, w=a.w, h=a.h + b.h))
                    changed = True
                    merged = True
                    break

                # If a is immediately below b:
                if _almost_eq(a.yt, b.yb):
                    rects.pop(j)
                    rects.pop(i)
                    rects.append(FreeRectTR(xr=b.xr, yt=b.yt, w=a.w, h=a.h + b.h))
                    changed = True
                    merged = True
                    break

            if not merged:
                i += 1

    return _prune_contained(rects)


# ----------------------------
# First-Fit Guillotine packer (single layer)
# ----------------------------

@dataclass
class Placed2DTR:
    xr: float  # placed rect's top-right corner x
    yt: float  # placed rect's top-right corner y
    w: float
    h: float
    rotated: bool


def _split_guillotine(
    fr: FreeRectTR,
    placed_w: float,
    placed_h: float,
    split_rule: str = "larger_leftover",
) -> List[FreeRectTR]:
    """
    Place at fr's top-right corner, then split remaining space into 2 free rects.
    Two canonical cut orders:
      A) vertical-first: left (fw-rw, fh) + bottom-right (rw, fh-rh)
      B) horizontal-first: left-top (fw-rw, rh) + bottom (fw, fh-rh)

    split_rule:
      - "larger_leftover": if leftover_w >= leftover_h do vertical-first else horizontal-first
      - "smaller_leftover": if leftover_w <= leftover_h do vertical-first else horizontal-first
    """
    fw, fh = fr.w, fr.h
    lw = fw - placed_w
    lh = fh - placed_h

    if lw < 0 or lh < 0:
        return []

    if split_rule == "larger_leftover":
        vertical_first = (lw >= lh)
    elif split_rule == "smaller_leftover":
        vertical_first = (lw <= lh)
    else:
        raise ValueError(f"Unknown split_rule: {split_rule}")

    out: List[FreeRectTR] = []

    if vertical_first:
        # Left (full height)
        if lw > 0:
            out.append(FreeRectTR(xr=fr.xr - placed_w, yt=fr.yt, w=lw, h=fh))
        # Bottom-right (width = placed_w)
        if lh > 0:
            out.append(FreeRectTR(xr=fr.xr, yt=fr.yt + placed_h, w=placed_w, h=lh))
    else:
        # Left-top (height = placed_h)
        if lw > 0 and placed_h > 0:
            out.append(FreeRectTR(xr=fr.xr - placed_w, yt=fr.yt, w=lw, h=placed_h))
        # Bottom (full width)
        if lh > 0:
            out.append(FreeRectTR(xr=fr.xr, yt=fr.yt + placed_h, w=fw, h=lh))

    return [r for r in out if r.w > 0 and r.h > 0]


def ff_guillotine_layer_top_right(
    layer_w: float,
    layer_h: float,
    rects: List[Tuple[str, Rect2D]],  # (id, (w,h))
    allow_rotate: bool = True,
    split_rule: str = "larger_leftover",
    do_merge: bool = True,
) -> Tuple[List[Placed2DTR], List[str]]:
    """
    First-Fit Guillotine for a single 2D bin (layer) with top-right origin.
    Returns (placed, unplaced_ids).
    """
    free_rects: List[FreeRectTR] = [FreeRectTR(xr=0.0, yt=0.0, w=layer_w, h=layer_h)]
    placed: List[Placed2DTR] = []
    unplaced: List[str] = []

    for rid, r in rects:
        candidate = _place_first_fit(free_rects, r, allow_rotate)
        if candidate is None:
            unplaced.append(rid)
            continue

        fr_idx, used_w, used_h, rotated = candidate
        fr = free_rects.pop(fr_idx)

        # Place at the free rectangle's top-right corner
        placed.append(Placed2DTR(xr=fr.xr, yt=fr.yt, w=used_w, h=used_h, rotated=rotated))

        # Split and update free list
        free_rects.extend(_split_guillotine(fr, used_w, used_h, split_rule=split_rule))
        free_rects = _prune_contained(free_rects)
        if do_merge:
            free_rects = _merge_guillotine(free_rects)

    return placed, unplaced


def _place_first_fit(
    free_rects: List[FreeRectTR],
    r: Rect2D,
    allow_rotate: bool,
) -> Optional[Tuple[int, float, float, bool]]:
    """
    Returns (free_index, used_w, used_h, rotated) for the first free rect that fits.
    """
    for i, fr in enumerate(free_rects):
        # no rotation
        if r.w <= fr.w and r.h <= fr.h:
            return (i, r.w, r.h, False)
        # rotate 90 degrees in-plane
        if allow_rotate and r.h <= fr.w and r.w <= fr.h:
            return (i, r.h, r.w, True)
    return None


# ----------------------------
# 3D wrapper: stack guillotine-packed layers in z
# ----------------------------

def pack_truck_ff_guillotine_top_right(
    truck: Truck_t,
    boxes: List[Box_t],
    *,
    allow_rotate_xy: bool = True,   # rotate in the floor plane (swap width/depth)
    sort_by: str = "footprint_desc",  # "footprint_desc" | "volume_desc" | "none"
    split_rule: str = "larger_leftover",
    do_merge: bool = True,
) -> Tuple[List[PlacedBox_t], List[Box_t]]:
    """
    Packs boxes into the truck by stacking 2D guillotine layers.

    Layering policy (simple, deterministic):
      - take remaining boxes (sorted)
      - choose layer_height = max height among remaining (i.e., the first box's height after sort by height desc)
      - pack as many as possible on the floor (width x depth) using FF-Guillotine
      - advance z by layer_height, repeat until height exhausted

    Coordinates:
      - x,y are returned in TOP-RIGHT-origin coordinates on each layer
      - z increases upward from 0 (bottom of truck)
    """
    # Choose sort order for packing attempts
    remaining = boxes[:]
    if sort_by == "footprint_desc":
        remaining.sort(key=lambda b: (b.width * b.depth), reverse=True)
    elif sort_by == "volume_desc":
        remaining.sort(key=lambda b: (b.width * b.depth * b.height), reverse=True)
    elif sort_by != "none":
        raise ValueError(f"Unknown sort_by: {sort_by}")

    placed3d: List[PlacedBox_t] = []
    unplaced_final: List[Box_t] = []

    z = 0.0
    # Keep going while we have boxes and vertical room
    while remaining and z < truck.height:
        # Greedy layer height choice: tallest remaining
        remaining.sort(key=lambda b: b.height, reverse=True)
        layer_height = remaining[0].height

        if z + layer_height > truck.height:
            # Anything left cannot fit vertically
            unplaced_final.extend(remaining)
            break

        # Prepare 2D rectangles for this layer (width x depth footprint).
        # (We allow all boxes whose height <= layer_height; since layer_height is max, that is all of them.)
        rects2d: List[Tuple[str, Rect2D]] = [(b.id, Rect2D(b.width, b.depth)) for b in remaining]

        placed2d, unplaced_ids = ff_guillotine_layer_top_right(
            layer_w=truck.width,
            layer_h=truck.depth,
            rects=rects2d,
            allow_rotate=allow_rotate_xy,
            split_rule=split_rule,
            do_merge=do_merge,
        )

        # Convert layer placements to PlacedBox_t and remove placed from remaining
        placed_ids = set()
        by_id = {b.id: b for b in remaining}

        for p in placed2d:
            b = by_id[p_id := _find_id_for_placement(p, by_id)]
            # rotation: 0 = no swap, 1 = swapped width/depth
            placed3d.append(
                PlacedBox_t(
                    id=b.id,
                    x=p.xr,         # top-right origin coord
                    y=p.yt,         # top-right origin coord
                    z=z,
                    rotation=1 if p.rotated else 0,
                )
            )
            placed_ids.add(b.id)

        # Update remaining/unplaced for next layer attempt
        new_remaining: List[Box_t] = []
        for b in remaining:
            if b.id not in placed_ids:
                new_remaining.append(b)
        remaining = new_remaining

        # If nothing placed, stop to avoid infinite loop
        if not placed_ids:
            unplaced_final.extend(remaining)
            break

        z += layer_height

    return placed3d, unplaced_final


def _find_id_for_placement(p: Placed2DTR, by_id: dict) -> str:
    """
    FF-Guillotine places items in order; a stable mapping is needed from placement back to an item id.
    This helper assumes rects are packed as (id, Rect2D) in the same order as `remaining`,
    and that ids are unique.

    In this implementation, we reconstruct by matching dimensions (with rotation awareness).
    If you can pass the id directly in the placement record, do that instead.
    """
    # Prefer exact match first
    for bid, b in by_id.items():
        if _almost_eq(p.w, b.width) and _almost_eq(p.h, b.depth) and not p.rotated:
            return bid
        if _almost_eq(p.w, b.depth) and _almost_eq(p.h, b.width) and p.rotated:
            return bid

    # Fallback: match by footprint only (can be ambiguous if duplicates)
    for bid, b in by_id.items():
        if _almost_eq(p.w * p.h, b.width * b.depth):
            return bid

    raise RuntimeError("Could not map 2D placement back to a box id (duplicate sizes likely).")
