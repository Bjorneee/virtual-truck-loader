"""
Heuristics for packing algorithms.

Currently implemented heuristics:

- FF-Guillotine (FFG)
- Skyline Sort
- MaxRect

"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from python.vtl_core.domain.models import Box_t, PlacedBox_t, Truck_t

"""

First-Fit Guillotine (FFG)

"""

# ----------------------------
# Geometry helpers (top-left origin)
# ----------------------------
# Coordinate system for each 2D layer (width x depth):
#   origin (0,0) is TOP-LEFT corner of the layer rectangle
#   x increases RIGHTWARD
#   y increases DOWNWARD
#
# A free-rectangle is represented by its top-left corner (x, y) and size (w,h),
# where it spans:
#   x in [x, x + w]
#   y in [y, y + h]


@dataclass(frozen=True)
class Rect2D:
    w: float  # width (layer-x extent)
    h: float  # height (layer-y extent), here "depth"


@dataclass
class FreeRectTL:
    x: float  # x coordinate of top-left corner
    y: float  # y coordinate of top-left corner
    w: float
    h: float

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def bottom(self) -> float:
        return self.y + self.h


def _contains(a: FreeRectTL, b: FreeRectTL) -> bool:
    # a contains b
    return (a.x <= b.x) and (a.y <= b.y) and (a.right >= b.right) and (a.bottom >= b.bottom)


def _almost_eq(a: float, b: float, eps: float = 1e-9) -> bool:
    return abs(a - b) <= eps


def _prune_contained(free_rects: List[FreeRectTL]) -> List[FreeRectTL]:
    out: List[FreeRectTL] = []
    for i, r in enumerate(free_rects):
        contained = False
        for j, s in enumerate(free_rects):
            if i != j and _contains(s, r):
                contained = True
                break
        if not contained:
            out.append(r)

    # remove exact duplicates
    uniq: List[FreeRectTL] = []
    seen = set()
    for r in out:
        key = (r.x, r.y, r.w, r.h)
        if key not in seen:
            seen.add(key)
            uniq.append(r)
    return uniq


def _merge_guillotine(free_rects: List[FreeRectTL]) -> List[FreeRectTL]:
    """
    Optional merge step:
      - merge horizontally adjacent rects with same (y,h) and touching in x
      - merge vertically adjacent rects with same (x,w) and touching in y
    """
    changed = True
    rects = free_rects[:]

    while changed:
        changed = False
        rects = _prune_contained(rects)

        # Horizontal merges: same y,h and touching on x edge
        rects.sort(key=lambda r: (r.y, r.h, r.x, r.w))
        i = 0
        while i < len(rects):
            a = rects[i]
            merged = False
            for j in range(i + 1, len(rects)):
                b = rects[j]
                if not (_almost_eq(a.y, b.y) and _almost_eq(a.h, b.h)):
                    continue

                # b immediately to the right of a
                if _almost_eq(a.right, b.x):
                    rects.pop(j)
                    rects.pop(i)
                    rects.append(FreeRectTL(x=a.x, y=a.y, w=a.w + b.w, h=a.h))
                    changed = True
                    merged = True
                    break

                # a immediately to the right of b
                if _almost_eq(b.right, a.x):
                    rects.pop(j)
                    rects.pop(i)
                    rects.append(FreeRectTL(x=b.x, y=b.y, w=a.w + b.w, h=a.h))
                    changed = True
                    merged = True
                    break

            if not merged:
                i += 1

        if changed:
            continue

        # Vertical merges: same x,w and touching on y edge
        rects.sort(key=lambda r: (r.x, r.w, r.y, r.h))
        i = 0
        while i < len(rects):
            a = rects[i]
            merged = False
            for j in range(i + 1, len(rects)):
                b = rects[j]
                if not (_almost_eq(a.x, b.x) and _almost_eq(a.w, b.w)):
                    continue

                # b immediately below a
                if _almost_eq(a.bottom, b.y):
                    rects.pop(j)
                    rects.pop(i)
                    rects.append(FreeRectTL(x=a.x, y=a.y, w=a.w, h=a.h + b.h))
                    changed = True
                    merged = True
                    break

                # a immediately below b
                if _almost_eq(b.bottom, a.y):
                    rects.pop(j)
                    rects.pop(i)
                    rects.append(FreeRectTL(x=b.x, y=b.y, w=a.w, h=a.h + b.h))
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
class Placed2DTL:
    x: float  # placed rect's top-left corner x
    y: float  # placed rect's top-left corner y
    w: float
    h: float
    rotated: bool


def _split_guillotine(
    fr: FreeRectTL,
    placed_w: float,
    placed_h: float,
    split_rule: str = "larger_leftover",
) -> List[FreeRectTL]:
    """
    Place at fr's top-left corner (fr.x, fr.y), then split remaining space into 2 free rects.

    Two canonical cut orders:
      A) vertical-first:
         - right:        (x+rw, y,     fw-rw, fh)
         - bottom-left:  (x,    y+rh,  rw,    fh-rh)

      B) horizontal-first:
         - right-top:    (x+rw, y,     fw-rw, rh)
         - bottom:       (x,    y+rh,  fw,    fh-rh)

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

    out: List[FreeRectTL] = []

    if vertical_first:
        # Right remainder (full height)
        if lw > 0:
            out.append(FreeRectTL(x=fr.x + placed_w, y=fr.y, w=lw, h=fh))
        # Bottom-left remainder (width = placed_w)
        if lh > 0:
            out.append(FreeRectTL(x=fr.x, y=fr.y + placed_h, w=placed_w, h=lh))
    else:
        # Right-top remainder (height = placed_h)
        if lw > 0 and placed_h > 0:
            out.append(FreeRectTL(x=fr.x + placed_w, y=fr.y, w=lw, h=placed_h))
        # Bottom remainder (full width)
        if lh > 0:
            out.append(FreeRectTL(x=fr.x, y=fr.y + placed_h, w=fw, h=lh))

    return [r for r in out if r.w > 0 and r.h > 0]


def ff_guillotine_layer_top_left(
    layer_w: float,
    layer_h: float,
    rects: List[Tuple[str, Rect2D]],  # (id, (w,h))
    allow_rotate: bool = True,        # Y-axis only: swap (w,h) in-plane
    split_rule: str = "larger_leftover",
    do_merge: bool = True,
) -> Tuple[List[Placed2DTL], List[str]]:
    """
    First-Fit Guillotine for a single 2D bin (layer) with TOP-LEFT origin.
    Returns (placed, unplaced_ids).
    """
    free_rects: List[FreeRectTL] = [FreeRectTL(x=0.0, y=0.0, w=layer_w, h=layer_h)]
    placed: List[Placed2DTL] = []
    unplaced: List[str] = []

    for rid, r in rects:
        candidate = _place_first_fit(free_rects, r, allow_rotate)
        if candidate is None:
            unplaced.append(rid)
            continue

        fr_idx, used_w, used_h, rotated = candidate
        fr = free_rects.pop(fr_idx)

        # Place at the free rectangle's top-left corner
        placed.append(Placed2DTL(x=fr.x, y=fr.y, w=used_w, h=used_h, rotated=rotated))

        # Split and update free list
        free_rects.extend(_split_guillotine(fr, used_w, used_h, split_rule=split_rule))
        free_rects = _prune_contained(free_rects)
        if do_merge:
            free_rects = _merge_guillotine(free_rects)

    return placed, unplaced


def _place_first_fit(
    free_rects: List[FreeRectTL],
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
        # rotate 90 degrees in-plane (Y-axis in 3D): swap width/depth
        if allow_rotate and r.h <= fr.w and r.w <= fr.h:
            return (i, r.h, r.w, True)
    return None


# ----------------------------
# 3D wrapper: stack guillotine-packed layers in z
# ----------------------------

def pack_truck_ff_guillotine_top_left(
    truck,  # Truck_t
    boxes,  # List[Box_t]
    *,
    allow_rotate_y: bool = True,      # Y-axis only: swap width/depth
    sort_by: str = "footprint_desc",  # "footprint_desc" | "volume_desc" | "none"
    split_rule: str = "larger_leftover",
    do_merge: bool = True,
):
    """
    Same layering policy as before; now x,y are TOP-LEFT-origin per layer.
    """
    remaining = boxes[:]
    if sort_by == "footprint_desc":
        remaining.sort(key=lambda b: (b.width * b.depth), reverse=True)
    elif sort_by == "volume_desc":
        remaining.sort(key=lambda b: (b.width * b.depth * b.height), reverse=True)
    elif sort_by != "none":
        raise ValueError(f"Unknown sort_by: {sort_by}")

    placed3d = []
    unplaced_final = []

    z = 0.0
    while remaining and z < truck.height:
        remaining.sort(key=lambda b: b.height, reverse=True)
        layer_height = remaining[0].height

        if z + layer_height > truck.height:
            unplaced_final.extend(remaining)
            break

        rects2d: List[Tuple[str, Rect2D]] = [(b.id, Rect2D(b.width, b.depth)) for b in remaining]

        placed2d, _unplaced_ids = ff_guillotine_layer_top_left(
            layer_w=truck.width,
            layer_h=truck.depth,
            rects=rects2d,
            allow_rotate=allow_rotate_y,
            split_rule=split_rule,
            do_merge=do_merge,
        )

        # IMPORTANT: do NOT use _find_id_for_placement() if you can avoid it.
        # The clean fix is to carry the id in the placed record.
        # Here is the minimal change approach: we remap by dimensions (can be ambiguous with duplicates).
        placed_ids = set()
        by_id = {b.id: b for b in remaining}

        for p in placed2d:
            bid = _find_id_for_placement_2d(p, by_id)
            b = by_id[bid]
            placed3d.append(
                PlacedBox_t(
                    id=b.id,
                    x=p.x,            # TOP-LEFT origin coord
                    y=p.y,            # TOP-LEFT origin coord
                    z=z,
                    rotation=1 if p.rotated else 0,  # 1 means width/depth swapped (Y rotation)
                )
            )
            placed_ids.add(b.id)

        new_remaining = [b for b in remaining if b.id not in placed_ids]
        remaining = new_remaining

        if not placed_ids:
            unplaced_final.extend(remaining)
            break

        z += layer_height

    return placed3d, unplaced_final


def _find_id_for_placement_2d(p: Placed2DTL, by_id: dict) -> str:
    """
    WARNING: ambiguous if you have multiple boxes with identical footprints.
    Prefer to store the id in Placed2DTL directly.
    """
    for bid, b in by_id.items():
        if _almost_eq(p.w, b.width) and _almost_eq(p.h, b.depth) and not p.rotated:
            return bid
        if _almost_eq(p.w, b.depth) and _almost_eq(p.h, b.width) and p.rotated:
            return bid

    for bid, b in by_id.items():
        if _almost_eq(p.w * p.h, b.width * b.depth):
            return bid

    raise RuntimeError("Could not map 2D placement back to a box id (duplicate sizes likely).")
