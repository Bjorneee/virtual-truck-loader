from __future__ import annotations

from typing import List, Optional, Tuple
from python.vtl_core.domain.models import (
    Box_t, 
    PlacedBox_t, 
    FreeRectTL, 
    SkylineSeg,
    Truck_t
)


_EPS = 1e-9

HeuristicResult = Tuple[List[PlacedBox_t], List[str], float, float, float]



def _fits(w: float, d: float, rect: FreeRectTL) -> bool:
    return w <= rect.w + _EPS and d <= rect.d + _EPS


"""
Remove degenerate rectangles and rectangles fully contained in others.
"""
def _ffg_prune_free_rects(rects: List[FreeRectTL]) -> List[FreeRectTL]:

    cleaned = [r for r in rects if r.w > _EPS and r.d > _EPS]

    pruned: List[FreeRectTL] = []
    for i, a in enumerate(cleaned):
        contained = False
        for j, b in enumerate(cleaned):
            if i == j:
                continue
            if (
                a.x >= b.x - _EPS and
                a.z >= b.z - _EPS and
                a.x + a.w <= b.x + b.w + _EPS and
                a.z + a.d <= b.z + b.d + _EPS
            ):
                contained = True
                break
        if not contained:
            pruned.append(a)

    # First-fit scan order: top to bottom, then left to right
    pruned.sort(key=lambda r: (r.z, r.x))
    return pruned


"""
Guillotine split after placing a box at the TOP-LEFT corner of rect.

Produces:
    - right remainder
    - bottom remainder
"""
def _ffg_split_free_rect(
    rect: FreeRectTL,
    placed_w: float,
    placed_d: float,
) -> List[FreeRectTL]:

    out: List[FreeRectTL] = []

    # Right remainder
    right_w = rect.w - placed_w
    if right_w > _EPS:
        out.append(
            FreeRectTL(
                x=rect.x + placed_w,
                z=rect.z,
                w=right_w,
                d=placed_d,
            )
        )

    # Bottom remainder
    bottom_d = rect.d - placed_d
    if bottom_d > _EPS:
        out.append(
            FreeRectTL(
                x=rect.x,
                z=rect.z + placed_d,
                w=rect.w,
                d=bottom_d,
            )
        )

    return out


"""
Allowed orientations for a layer:
    rotation 0: (width, depth)
    rotation 1: (depth, width)  -> Y-axis rotation

Returns:
    (placed_width, placed_depth, rotation_code)
"""
def _choose_orientation(box: Box_t, rect: FreeRectTL) -> Optional[Tuple[float, float, int]]:

    candidates: List[Tuple[float, float, int, float]] = []

    # Original orientation
    if _fits(box.width, box.depth, rect):
        waste = (rect.w - box.width) * (rect.d - box.depth)
        candidates.append((box.width, box.depth, 0, waste))

    # Y-axis rotation only
    if _fits(box.depth, box.width, rect):
        waste = (rect.w - box.depth) * (rect.d - box.width)
        candidates.append((box.depth, box.width, 1, waste))

    if not candidates:
        return None

    # Prefer lower waste, then non-rotated
    candidates.sort(key=lambda c: (c[3], c[2]))
    w, d, rot, _ = candidates[0]
    return (w, d, rot)


"""
Returns:
    (free_rect_index, x, z, placed_width, placed_depth, rotation)

rotation:
    0 = original footprint (width, depth)
    1 = Y-rotated footprint (depth, width)
"""
def _find_best_position_for_box_tl(
    box: Box_t,
    free_rects: List[FreeRectTL],
    allow_y_rotation: bool,
) -> Optional[Tuple[int, float, float, float, float, int]]:

    best: Optional[Tuple[float, float, float, float, float, int, int]] = None
    # Stored as:
    # (area_fit, short_side_fit, x, z, w, d, rotation, rect_index)

    orientations = [(box.width, box.depth, 0)]
    if allow_y_rotation and abs(box.width - box.depth) > _EPS:
        orientations.append((box.depth, box.width, 1))

    for i, fr in enumerate(free_rects):
        for bw, bd, rot in orientations:
            if bw <= fr.w + _EPS and bd <= fr.d + _EPS:
                area_fit = (fr.w * fr.d) - (bw * bd)
                short_side_fit = min(fr.w - bw, fr.d - bd)

                candidate = (
                    area_fit,
                    short_side_fit,
                    fr.x,
                    fr.z,
                    bw,
                    bd,
                    rot,
                    i,
                )

                if best is None or candidate < best:
                    best = candidate

    if best is None:
        return None

    _, _, x, z, w, d, rot, rect_index = best
    return rect_index, x, z, w, d, rot


def _rects_intersect(a: FreeRectTL, b: FreeRectTL) -> bool:
    return not (
        b.x >= a.right - _EPS or
        b.right <= a.x + _EPS or
        b.z >= a.bottom - _EPS or
        b.bottom <= a.z + _EPS
    )


"""
Split a free rectangle by carving out the used rectangle area.
Produces up to four rectangles: top, bottom, left, right.
"""
def _mr_split_free_rect(
    free_rect: FreeRectTL,
    used_rect: FreeRectTL,
) -> List[FreeRectTL]:

    result: List[FreeRectTL] = []

    # Top slice
    if used_rect.z > free_rect.z + _EPS:
        result.append(
            FreeRectTL(
                x=free_rect.x,
                z=free_rect.z,
                w=free_rect.w,
                d=used_rect.z - free_rect.z,
            )
        )

    # Bottom slice
    if used_rect.bottom < free_rect.bottom - _EPS:
        result.append(
            FreeRectTL(
                x=free_rect.x,
                z=used_rect.bottom,
                w=free_rect.w,
                d=free_rect.bottom - used_rect.bottom,
            )
        )

    # Left slice
    if used_rect.x > free_rect.x + _EPS:
        left_z0 = max(free_rect.z, used_rect.z)
        left_z1 = min(free_rect.bottom, used_rect.bottom)
        if left_z1 - left_z0 > _EPS:
            result.append(
                FreeRectTL(
                    x=free_rect.x,
                    z=left_z0,
                    w=used_rect.x - free_rect.x,
                    d=left_z1 - left_z0,
                )
            )

    # Right slice
    if used_rect.right < free_rect.right - _EPS:
        right_z0 = max(free_rect.z, used_rect.z)
        right_z1 = min(free_rect.bottom, used_rect.bottom)
        if right_z1 - right_z0 > _EPS:
            result.append(
                FreeRectTL(
                    x=used_rect.right,
                    z=right_z0,
                    w=free_rect.right - used_rect.right,
                    d=right_z1 - right_z0,
                )
            )

    return [r for r in result if r.w > _EPS and r.d > _EPS]


def _contains(a: FreeRectTL, b: FreeRectTL) -> bool:
    return (
        b.x >= a.x - _EPS and
        b.z >= a.z - _EPS and
        b.right <= a.right + _EPS and
        b.bottom <= a.bottom + _EPS
    )


"""
Remove redundant free rectangles fully contained inside others.
Also removes degenerate rectangles.
"""
def _mr_prune_free_rects(rects: List[FreeRectTL]) -> List[FreeRectTL]:

    pruned: List[FreeRectTL] = []

    for i, r in enumerate(rects):
        if r.w <= _EPS or r.d <= _EPS:
            continue

        contained = False
        for j, other in enumerate(rects):
            if i == j:
                continue
            if _contains(other, r):
                contained = True
                break

        if not contained:
            pruned.append(r)

    return pruned


"""
Returns:
    (seg_index, x, z, placed_width, placed_depth, rotation)

rotation:
    0 = (width, depth)
    1 = (depth, width)
"""
def _skyline_find_position(
    skyline: List[SkylineSeg],
    box: Box_t,
    truck_depth: float,
) -> Optional[Tuple[int, float, float, float, float, int]]:

    best: Optional[Tuple[float, float, float, int, float, float, int]] = None
    # (top_z, waste, x, seg_index, bw, bd, rotation)

    orientations = [
        (box.width, box.depth, 0),
    ]

    if abs(box.width - box.depth) > _EPS:
        orientations.append((box.depth, box.width, 1))

    for i, seg in enumerate(skyline):
        for bw, bd, rot in orientations:
            fit_z = _skyline_compute_fit(skyline, i, bw)
            if fit_z is None:
                continue

            if fit_z + bd > truck_depth + _EPS:
                continue

            waste = _skyline_waste(skyline, i, bw, fit_z)

            candidate = (fit_z, waste, seg.x, i, bw, bd, rot)

            if best is None or candidate < best:
                best = candidate

    if best is None:
        return None

    fit_z, _, x, i, bw, bd, rot = best
    return i, x, fit_z, bw, bd, rot


"""
Starting from skyline[start_idx], determines the z where a box of needed_width
can sit. Returns the max z across covered skyline segments, or None if not enough width.
"""
def _skyline_compute_fit(
    skyline: List[SkylineSeg],
    start_idx: int,
    needed_width: float,
) -> Optional[float]:

    width_left = needed_width
    j = start_idx
    max_z = skyline[start_idx].z
    x_start = skyline[start_idx].x
    x_end = x_start + needed_width

    while j < len(skyline) and skyline[j].x < x_end - _EPS:
        max_z = max(max_z, skyline[j].z)
        width_left -= skyline[j].w
        j += 1

    if width_left > _EPS:
        return None

    return max_z


"""
Waste area under the placed rectangle and above the covered skyline segments.
Used as tiebreaker after lowest z.
"""
def _skyline_waste(
    skyline: List[SkylineSeg],
    start_idx: int,
    width: float,
    base_z: float,
) -> float:

    waste = 0.0
    x_end = skyline[start_idx].x + width
    j = start_idx

    while j < len(skyline) and skyline[j].x < x_end - _EPS:
        overlap_start = max(skyline[j].x, skyline[start_idx].x)
        overlap_end = min(skyline[j].x + skyline[j].w, x_end)
        overlap_w = max(0.0, overlap_end - overlap_start)
        waste += overlap_w * (base_z - skyline[j].z)
        j += 1

    return waste


"""
Inserts a new skyline level for the placed box footprint [x, x+w) at height z+d.
Removes/adjusts overlapped skyline segments.
"""
def _skyline_add_level(
    skyline: List[SkylineSeg],
    seg_index: int,
    x: float,
    z: float,
    w: float,
    d: float,
) -> None:

    new_seg = SkylineSeg(x=x, z=z + d, w=w)
    end_x = x + w

    updated: List[SkylineSeg] = []
    inserted = False

    for seg in skyline:
        seg_start = seg.x
        seg_end = seg.x + seg.w

        if seg_end <= x + _EPS or seg_start >= end_x - _EPS:
            if not inserted and seg_start >= end_x - _EPS:
                updated.append(new_seg)
                inserted = True
            updated.append(seg)
            continue

        # Left remainder
        if seg_start < x - _EPS:
            updated.append(SkylineSeg(seg_start, seg.z, x - seg_start))

        # Insert new segment once
        if not inserted:
            updated.append(new_seg)
            inserted = True

        # Right remainder
        if seg_end > end_x + _EPS:
            updated.append(SkylineSeg(end_x, seg.z, seg_end - end_x))

    if not inserted:
        updated.append(new_seg)

    skyline[:] = updated


"""
Merge adjacent skyline segments with the same z.
"""
def _skyline_merge(skyline: List[SkylineSeg]) -> None:
    
    if not skyline:
        return

    skyline.sort(key=lambda s: s.x)

    merged: List[SkylineSeg] = [skyline[0]]

    for seg in skyline[1:]:
        last = merged[-1]
        if abs(last.z - seg.z) <= _EPS and abs((last.x + last.w) - seg.x) <= _EPS:
            last.w += seg.w
        else:
            merged.append(seg)

    skyline[:] = merged

def _dims_from_rotation(box: Box_t, rotation: int) -> Tuple[float, float]:
    if rotation == 1:
        return box.depth, box.width
    return box.width, box.depth


def _compute_local_extents(anchor: Box_t, placed: List[PlacedBox_t]) -> Tuple[float, float]:
    """
    Returns the local used envelope:
        used_x = max(x + placed_width)
        used_z = max(z + placed_depth)

    `placed` is expected to still be in local region coordinates.
    """
    used_x = 0.0
    used_z = 0.0

    for pb in placed:
        w, d = _dims_from_rotation(anchor, pb.rotation)
        used_x = max(used_x, pb.x + w)
        used_z = max(used_z, pb.z + d)

    return used_x, used_z


def _translate_placements(placed: List[PlacedBox_t], dx: float, dz: float) -> None:
    for pb in placed:
        pb.x += dx
        pb.z += dz


def _sort_key(box: Box_t):
    return (
        -box.height,
        -(box.footprint),
        -(box.volume),
        -(box.priority if box.priority is not None else 0.0),
        box.id,
    )


def _split_same_type_prefix(boxes: List[Box_t], sort_boxes: bool) -> Tuple[List[Box_t], List[Box_t], Box_t]:
    """
    Returns:
        batch     : maximal prefix of boxes equal to boxes[0]
        remainder : all boxes after that prefix
        anchor    : first box in batch
    """
    if not boxes:
        raise ValueError("No boxes provided.")

    anchor = boxes[0]
    batch: List[Box_t] = []
    i = 0

    while i < len(boxes) and boxes[i] == anchor:
        batch.append(boxes[i])
        i += 1

    remainder = boxes[i:]

    if sort_boxes:
        # Preserve type boundary: sort only within the same-type batch.
        batch = sorted(batch, key=_sort_key)

    return batch, remainder, anchor


def _height_cap(truck: Truck_t, layer_height: Optional[float]) -> float:
    """
    truck.height is interpreted as the vertical space available for the current sub-truck.
    layer_y is only an absolute placement coordinate and is not subtracted here.
    """
    if truck.width <= 0 or truck.depth <= 0 or truck.height <= 0:
        return 0.0

    if layer_height is None:
        return truck.height

    return min(layer_height, truck.height)


def _placed_rects_from_batch(placed: List[PlacedBox_t], anchor: Box_t) -> List[Tuple[float, float, float, float]]:
    """
    Convert placements into footprint rects (x, z, w, d) using the batch anchor dimensions.
    rotation:
      0 -> (width, depth)
      1 -> (depth, width)
    """
    rects: List[Tuple[float, float, float, float]] = []

    for pb in placed:
        if pb.rotation == 1:
            w, d = anchor.depth, anchor.width
        else:
            w, d = anchor.width, anchor.depth

        rects.append((pb.x, pb.z, w, d))

    return rects


def _largest_complete_top_left_rectangle(
    placed_rects: List[Tuple[float, float, float, float]],
    truck_width: float,
    truck_depth: float,
) -> Tuple[float, float]:
    """
    Returns (x_cursor, z_cursor) for the largest complete top-left-supported rectangle.

    A rectangle [0, x_cursor] x [0, z_cursor] is "complete" iff every elementary cell inside
    it is covered by placed footprints.
    """
    if not placed_rects:
        return 0.0, 0.0

    xs = {0.0}
    zs = {0.0}

    for x, z, w, d in placed_rects:
        xs.add(x)
        xs.add(x + w)
        zs.add(z)
        zs.add(z + d)

    xs = sorted(v for v in xs if v <= truck_width + _EPS)
    zs = sorted(v for v in zs if v <= truck_depth + _EPS)

    def cell_is_covered(x0: float, x1: float, z0: float, z1: float) -> bool:
        cx = (x0 + x1) / 2.0
        cz = (z0 + z1) / 2.0

        for rx, rz, rw, rd in placed_rects:
            if rx - _EPS <= cx <= rx + rw + _EPS and rz - _EPS <= cz <= rz + rd + _EPS:
                return True
        return False

    best_x = 0.0
    best_z = 0.0

    for xi in range(1, len(xs)):
        for zi in range(1, len(zs)):
            x_cursor = xs[xi]
            z_cursor = zs[zi]

            full = True
            for ax in range(xi):
                for az in range(zi):
                    if not cell_is_covered(xs[ax], xs[ax + 1], zs[az], zs[az + 1]):
                        full = False
                        break
                if not full:
                    break

            if not full:
                continue

            area = x_cursor * z_cursor
            best_area = best_x * best_z

            if area > best_area + _EPS:
                best_x = x_cursor
                best_z = z_cursor
            elif abs(area - best_area) <= _EPS:
                if x_cursor > best_x + _EPS or (
                    abs(x_cursor - best_x) <= _EPS and z_cursor > best_z + _EPS
                ):
                    best_x = x_cursor
                    best_z = z_cursor

    return best_x, best_z


def _finalize_batch_result(
    boxes: List[Box_t],
    batch_failures: List[Box_t],
    remainder: List[Box_t],
    placed: List[PlacedBox_t],
    notes: List[str],
    used_layer_height: float,
    anchor: Box_t,
    packed_by: str,
    truck: Truck_t,
) -> HeuristicResult:
    """
    Mutates boxes so that only current-batch failures + untouched remainder remain.
    Computes complete support rectangle cursors.
    """
    boxes[:] = batch_failures + remainder

    placed_rects = _placed_rects_from_batch(placed, anchor)
    x_cursor, z_cursor = _largest_complete_top_left_rectangle(
        placed_rects=placed_rects,
        truck_width=truck.width,
        truck_depth=truck.depth,
    )

    notes.append(
        f"Packed by: {packed_by} | placed={len(placed)} | "
        f"used_h={used_layer_height:.3f} | support=({x_cursor:.3f}, {z_cursor:.3f})"
    )

    return placed, notes, used_layer_height, x_cursor, z_cursor