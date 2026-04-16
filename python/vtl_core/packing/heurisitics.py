from __future__ import annotations

from typing import List, Optional, Tuple

from python.vtl_core.domain.models import Box_t, PlacedBox_t, Truck_t
from python.vtl_core.domain.models import FreeRectTL, SkylineSeg

from python.vtl_core.utils import (
    _ffg_prune_free_rects,
    _ffg_split_free_rect,
    _choose_orientation,
    _find_best_position_for_box_tl,
    _rects_intersect,
    _mr_split_free_rect,
    _mr_prune_free_rects,
    _skyline_find_position,
    _skyline_add_level,
    _skyline_merge,
)

_EPS = 1e-9

HeuristicResult = Tuple[List[PlacedBox_t], List[str], float, float, float]


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


def ff_row_pack(
    truck: Truck_t,
    boxes: List[Box_t],
    layer_y: float = 0.0,
    layer_height: Optional[float] = None,
    sort_boxes: bool = True,
) -> HeuristicResult:
    """
    Packs exactly one layer of exactly one box type using first-fit row packing.
    Stops at the first different box type by only considering the maximal prefix of boxes[0].
    """
    placed: List[PlacedBox_t] = []
    notes: List[str] = []

    if not boxes:
        return placed, notes, 0.0, 0.0, 0.0

    batch, remainder, anchor = _split_same_type_prefix(boxes, sort_boxes)
    height_cap = _height_cap(truck, layer_height)
    if height_cap <= _EPS:
        notes.append("No available vertical space in current sub-truck.")
        return _finalize_batch_result(
            boxes, batch, remainder, placed, notes, 0.0, anchor, "FFR", truck
        )

    batch_failures: List[Box_t] = []
    used_layer_height = 0.0

    row_z = 0.0
    row_depth = 0.0
    row_x = 0.0
    has_row = False

    for box in batch:
        if box.height > height_cap + _EPS:
            batch_failures.append(box)
            notes.append(f"Box [{box.id}] exceeds height cap {height_cap:.3f}.")
            continue

        if box.width > truck.width + _EPS or box.depth > truck.depth + _EPS:
            batch_failures.append(box)
            notes.append(f"Box [{box.id}] footprint does not fit current sub-truck floor.")
            continue

        if not has_row:
            placed.append(
                PlacedBox_t(
                    id=box.id,
                    x=0.0,
                    y=layer_y,
                    z=0.0,
                    rotation=0,
                )
            )
            row_x = box.width
            row_z = 0.0
            row_depth = box.depth
            has_row = True
            used_layer_height = max(used_layer_height, box.height)
            continue

        # Same row
        if row_x + box.width <= truck.width + _EPS and box.depth <= row_depth + _EPS:
            placed.append(
                PlacedBox_t(
                    id=box.id,
                    x=row_x,
                    y=layer_y,
                    z=row_z,
                    rotation=0,
                )
            )
            row_x += box.width
            used_layer_height = max(used_layer_height, box.height)
            continue

        # New row
        new_row_z = row_z + row_depth
        if new_row_z + box.depth <= truck.depth + _EPS:
            placed.append(
                PlacedBox_t(
                    id=box.id,
                    x=0.0,
                    y=layer_y,
                    z=new_row_z,
                    rotation=0,
                )
            )
            row_z = new_row_z
            row_x = box.width
            row_depth = box.depth
            used_layer_height = max(used_layer_height, box.height)
            continue

        batch_failures.append(box)
        notes.append(f"Box [{box.id}] could not be placed in current batch/layer.")

    return _finalize_batch_result(
        boxes, batch_failures, remainder, placed, notes, used_layer_height, anchor, "FFR", truck
    )


def ff_guillotine_pack(
    truck: Truck_t,
    boxes: List[Box_t],
    layer_y: float = 0.0,
    layer_height: Optional[float] = None,
    sort_boxes: bool = True,
) -> HeuristicResult:
    """
    Packs exactly one layer of exactly one box type using first-fit guillotine.
    """
    notes: List[str] = []
    placed: List[PlacedBox_t] = []

    if not boxes:
        return placed, notes, 0.0, 0.0, 0.0

    batch, remainder, anchor = _split_same_type_prefix(boxes, sort_boxes)
    height_cap = _height_cap(truck, layer_height)
    if height_cap <= _EPS:
        notes.append("No available vertical space in current sub-truck.")
        return _finalize_batch_result(
            boxes, batch, remainder, placed, notes, 0.0, anchor, "FFG", truck
        )

    free_rects: List[FreeRectTL] = [FreeRectTL(0.0, 0.0, truck.width, truck.depth)]
    batch_failures: List[Box_t] = []
    used_layer_height = 0.0

    for box in batch:
        if box.height > height_cap + _EPS:
            batch_failures.append(box)
            notes.append(f"Box [{box.id}] exceeds height cap {height_cap:.3f}.")
            continue

        placed_this_box = False

        for i, rect in enumerate(free_rects):
            orient = _choose_orientation(box, rect)
            if orient is None:
                continue

            pw, pd, rot = orient
            px = rect.x
            pz = rect.z

            placed.append(
                PlacedBox_t(
                    id=box.id,
                    x=px,
                    y=layer_y,
                    z=pz,
                    rotation=rot,
                )
            )

            new_rects = free_rects[:i] + free_rects[i + 1 :]
            new_rects.extend(_ffg_split_free_rect(rect, pw, pd))
            free_rects = _ffg_prune_free_rects(new_rects)

            used_layer_height = max(used_layer_height, box.height)
            placed_this_box = True
            break

        if not placed_this_box:
            batch_failures.append(box)
            notes.append(f"Box [{box.id}] could not be placed in current batch/layer.")

    return _finalize_batch_result(
        boxes, batch_failures, remainder, placed, notes, used_layer_height, anchor, "FFG", truck
    )


def maxrects_pack(
    truck: Truck_t,
    boxes: List[Box_t],
    layer_y: float = 0.0,
    layer_height: Optional[float] = None,
    allow_y_rotation: bool = True,
    sort_boxes: bool = True,
) -> HeuristicResult:
    """
    Packs exactly one layer of exactly one box type using MaxRects.
    """
    placed: List[PlacedBox_t] = []
    notes: List[str] = []

    if not boxes:
        return placed, notes, 0.0, 0.0, 0.0

    batch, remainder, anchor = _split_same_type_prefix(boxes, sort_boxes)
    height_cap = _height_cap(truck, layer_height)
    if height_cap <= _EPS:
        notes.append("No available vertical space in current sub-truck.")
        return _finalize_batch_result(
            boxes, batch, remainder, placed, notes, 0.0, anchor, "MAX", truck
        )

    free_rects: List[FreeRectTL] = [FreeRectTL(0.0, 0.0, truck.width, truck.depth)]
    batch_failures: List[Box_t] = []
    used_layer_height = 0.0

    for box in batch:
        if box.height > height_cap + _EPS:
            batch_failures.append(box)
            notes.append(f"Box [{box.id}] exceeds height cap {height_cap:.3f}.")
            continue

        placement = _find_best_position_for_box_tl(
            box=box,
            free_rects=free_rects,
            allow_y_rotation=allow_y_rotation,
        )

        if placement is None:
            batch_failures.append(box)
            notes.append(f"Box [{box.id}] could not be placed in current batch/layer.")
            continue

        _, px, pz, pw, pd, rotation = placement

        placed.append(
            PlacedBox_t(
                id=box.id,
                x=px,
                y=layer_y,
                z=pz,
                rotation=rotation,
            )
        )
        used_layer_height = max(used_layer_height, box.height)

        new_free_rects: List[FreeRectTL] = []
        placed_rect = FreeRectTL(px, pz, pw, pd)

        for fr in free_rects:
            if not _rects_intersect(fr, placed_rect):
                new_free_rects.append(fr)
                continue

            new_free_rects.extend(_mr_split_free_rect(fr, placed_rect))

        free_rects = _mr_prune_free_rects(new_free_rects)

    return _finalize_batch_result(
        boxes, batch_failures, remainder, placed, notes, used_layer_height, anchor, "MAX", truck
    )


def skyline_pack(
    truck: Truck_t,
    boxes: List[Box_t],
    layer_y: float = 0.0,
    layer_height: Optional[float] = None,
    sort_boxes: bool = True,
) -> HeuristicResult:
    """
    Packs exactly one layer of exactly one box type using Skyline.
    """
    placed: List[PlacedBox_t] = []
    notes: List[str] = []

    if not boxes:
        return placed, notes, 0.0, 0.0, 0.0

    batch, remainder, anchor = _split_same_type_prefix(boxes, sort_boxes)
    height_cap = _height_cap(truck, layer_height)
    if height_cap <= _EPS:
        notes.append("No available vertical space in current sub-truck.")
        return _finalize_batch_result(
            boxes, batch, remainder, placed, notes, 0.0, anchor, "SKY", truck
        )

    skyline: List[SkylineSeg] = [SkylineSeg(0.0, 0.0, truck.width)]
    batch_failures: List[Box_t] = []
    used_layer_height = 0.0

    for box in batch:
        if box.height > height_cap + _EPS:
            batch_failures.append(box)
            notes.append(f"Box [{box.id}] exceeds height cap {height_cap:.3f}.")
            continue

        best = _skyline_find_position(skyline, box, truck.depth)

        if best is None:
            batch_failures.append(box)
            notes.append(f"Box [{box.id}] could not be placed in current batch/layer.")
            continue

        seg_index, px, pz, bw, bd, rotation = best

        placed.append(
            PlacedBox_t(
                id=box.id,
                x=px,
                y=layer_y,
                z=pz,
                rotation=rotation,
            )
        )
        used_layer_height = max(used_layer_height, box.height)

        _skyline_add_level(
            skyline=skyline,
            seg_index=seg_index,
            x=px,
            z=pz,
            w=bw,
            d=bd,
        )
        _skyline_merge(skyline)

    return _finalize_batch_result(
        boxes, batch_failures, remainder, placed, notes, used_layer_height, anchor, "SKY", truck
    )