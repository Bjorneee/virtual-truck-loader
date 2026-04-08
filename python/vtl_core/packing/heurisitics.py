"""
Heuristics for packing algorithms.

Currently implemented heuristics:

- FF-Guillotine (FFG)
- Skyline Sort
- MaxRect

"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum, auto

from python.vtl_core.domain.models import Box_t, PlacedBox_t, Truck_t

# Enumerations used to select desired layer-packing heuristic
class Heuristics(Enum):
    FF  = auto()
    FFG = auto()
    MAX = auto()
    SKY = auto()


@dataclass
class Row:
    z_start: float
    depth_used: float = 0.0
    x_cursor: float = 0.0


@dataclass
class Layer:
    y_start: float
    height: float
    depth_cursor: float = 0.0
    rows: List[Row] = field(default_factory=list)


def first_fit_pack(truck: Truck_t, boxes: List[Box_t]) -> List[PlacedBox_t]:
    """
    Basic layered first-fit packing using internal dataclasses.

    Inputs:
        truck: Truck_t
        boxes: List[Box_t], expected to be sorted by descending height

    Output:
        Tuple[List[PlacedBox_t], List[str]]

    Side effect:
        The original `boxes` list is modified in place so that after packing,
        it contains only boxes that could not be placed.

    Notes:
        - No rotation is performed in this version.
        - No weight-limit enforcement yet.
        - Uses a simple layered shelf/row strategy.
    """

    placed: List[PlacedBox_t] = []
    layers: List[Layer] = []
    unplaced: List[Box_t] = []
    notes: List[str] = []

    for box in boxes:

        print("Attempting: [" + box.id + "]")
        # Reject immediately if the box cannot fit in the truck at all
        if (
            box.width > truck.width
            or box.height > truck.height
            or box.depth > truck.depth
        ):
            unplaced.append(box)
            notes.append("Box: [" + box.id + "] does not fit in truck.")
            print("Failure on: [" + box.id + "]")
            continue

        was_placed = False

        # 1) Try to place in existing rows of existing layers
        for layer in layers:
            if box.height > layer.height:
                continue

            for row in layer.rows:
                fits_width = row.x_cursor + box.width <= truck.width
                fits_row_depth = box.depth <= row.depth_used

                if fits_width and fits_row_depth:
                    placed.append(
                        PlacedBox_t(
                            id=box.id,
                            x=row.x_cursor,
                            y=layer.y_start,
                            z=row.z_start,
                            rotation=0,
                        )
                    )
                    row.x_cursor += box.width
                    was_placed = True
                    print("Box placed: [" + box.id + "]")
                    break

            if was_placed:
                break

            # 2) Try creating a new row in this existing layer
            if layer.depth_cursor + box.depth <= truck.depth:
                new_row = Row(
                    z_start=layer.depth_cursor,
                    depth_used=box.depth,
                    x_cursor=box.width,
                )
                layer.rows.append(new_row)
                layer.depth_cursor += box.depth

                placed.append(
                    PlacedBox_t(
                        id=box.id,
                        x=0.0,
                        y=layer.y_start,
                        z=new_row.z_start,
                        rotation=0,
                    )
                )
                was_placed = True
                print("Box placed: [" + box.id + "]")
                break

        if was_placed:
            continue

        # 3) Try creating a new layer
        used_height = sum(layer.height for layer in layers)
        if used_height + box.height <= truck.height:
            new_layer = Layer(
                y_start=used_height,
                height=box.height,
                depth_cursor=box.depth,
                rows=[Row(z_start=0.0, depth_used=box.depth, x_cursor=box.width)],
            )
            layers.append(new_layer)

            placed.append(
                PlacedBox_t(
                    id=box.id,
                    x=0.0,
                    y=new_layer.y_start,
                    z=0.0,
                    rotation=0,
                )
            )
            print("Box placed: [" + box.id + "]")
        else:
            unplaced.append(box)
            print("Failure on: [" + box.id + "]")

    # Modify input list in place to keep only boxes that could not be placed
    boxes[:] = unplaced
    notes.append("Packed with First-Fit")

    return [placed, notes]




@dataclass
class FreeRectTL:
    """
    Top-left-origin free rectangle on a single floor layer.

    Coordinate system for a layer:
      origin = top-left
      x increases to the right
      z increases downward / forward into the truck floor plane

    The rectangle spans:
      x in [x, x + w)
      z in [z, z + d)
    """
    x: float
    z: float
    w: float
    d: float


@dataclass
class LayerPlacement:
    box: Box_t
    x: float
    z: float
    rotation: int   # 0 = no floor rotation, 1 = rotated around Y (swap width/depth)


_EPS = 1e-9


def _fits_in_rect(box_w: float, box_d: float, rect: FreeRectTL) -> bool:
    return box_w <= rect.w + _EPS and box_d <= rect.d + _EPS


def _rect_area(rect: FreeRectTL) -> float:
    return rect.w * rect.d


def _prune_free_rects(rects: List[FreeRectTL]) -> List[FreeRectTL]:
    """
    Remove degenerate rectangles and rectangles fully contained by others.
    """
    cleaned: List[FreeRectTL] = []

    for r in rects:
        if r.w <= _EPS or r.d <= _EPS:
            continue
        cleaned.append(r)

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

    # Stable top-left ordering
    pruned.sort(key=lambda r: (r.z, r.x, r.d * r.w))
    return pruned


def _split_guillotine_top_left(
    free_rect: FreeRectTL,
    placed_x: float,
    placed_z: float,
    placed_w: float,
    placed_d: float,
) -> List[FreeRectTL]:
    """
    Guillotine split for a box placed at the TOP-LEFT of free_rect.

    We produce:
      1) right remainder
      2) bottom remainder

    This preserves top-left-origin behavior cleanly.
    """
    out: List[FreeRectTL] = []

    # Right strip
    right_w = free_rect.w - placed_w
    if right_w > _EPS:
        out.append(
            FreeRectTL(
                x=placed_x + placed_w,
                z=placed_z,
                w=right_w,
                d=placed_d,
            )
        )

    # Bottom strip
    bottom_d = free_rect.d - placed_d
    if bottom_d > _EPS:
        out.append(
            FreeRectTL(
                x=placed_x,
                z=placed_z + placed_d,
                w=free_rect.w,
                d=bottom_d,
            )
        )

    return out


def _choose_orientation_for_rect(box: Box_t, rect: FreeRectTL) -> Optional[Tuple[float, float, int]]:
    """
    Returns (placed_width, placed_depth, rotation_code) for the first valid
    floor orientation in this rectangle.

    rotation_code:
      0 -> original (width, depth)
      1 -> Y-axis 90 degree rotation (depth, width)

    Preference:
      - first-fit
      - if both fit, choose the one with larger used edge alignment / less waste
    """
    candidates: List[Tuple[float, float, int, float]] = []

    # No floor rotation
    if _fits_in_rect(box.width, box.depth, rect):
        waste = (rect.w - box.width) * (rect.d - box.depth)
        candidates.append((box.width, box.depth, 0, waste))

    # Y-axis rotation only: swap width and depth
    if _fits_in_rect(box.depth, box.width, rect):
        waste = (rect.w - box.depth) * (rect.d - box.width)
        candidates.append((box.depth, box.width, 1, waste))

    if not candidates:
        return None

    # Smaller waste first, then non-rotated first for stability
    candidates.sort(key=lambda t: (t[3], t[2]))
    w, d, rot, _ = candidates[0]
    return (w, d, rot)


def _pack_single_layer_ffg(
    layer_boxes: List[Box_t],
    layer_width: float,
    layer_depth: float,
) -> Tuple[List[LayerPlacement], List[Box_t], List[str]]:
    """
    Packs as many boxes as possible into one 2D layer using a top-left-origin
    first-fit guillotine heuristic.

    Returns:
      placements in this layer,
      boxes that did NOT fit this layer,
      notes
    """
    free_rects: List[FreeRectTL] = [FreeRectTL(0.0, 0.0, layer_width, layer_depth)]
    placed: List[LayerPlacement] = []
    unplaced: List[Box_t] = []
    notes: List[str] = []

    for box in layer_boxes:
        placed_this_box = False

        # First-fit: scan free rects in top-left order
        for idx, rect in enumerate(free_rects):
            orient = _choose_orientation_for_rect(box, rect)
            if orient is None:
                continue

            pw, pd, rot = orient

            # Place at top-left corner of this free rectangle
            px = rect.x
            pz = rect.z

            placed.append(
                LayerPlacement(
                    box=box,
                    x=px,
                    z=pz,
                    rotation=rot,
                )
            )

            new_rects = free_rects[:idx] + free_rects[idx + 1:]
            new_rects.extend(
                _split_guillotine_top_left(
                    free_rect=rect,
                    placed_x=px,
                    placed_z=pz,
                    placed_w=pw,
                    placed_d=pd,
                )
            )

            free_rects = _prune_free_rects(new_rects)
            placed_this_box = True
            break

        if not placed_this_box:
            unplaced.append(box)

    if placed:
        used_area = sum(
            (lp.box.width * lp.box.depth) if lp.rotation == 0 else (lp.box.depth * lp.box.width)
            for lp in placed
        )
        layer_area = layer_width * layer_depth
        notes.append(
            f"Packed layer with {len(placed)} box(es); floor utilization = {used_area / layer_area:.2%}"
        )
    else:
        notes.append("No boxes fit in the current layer.")

    return placed, unplaced, notes


def ff_guillotine_pack(
    truck: Truck_t,
    boxes: List[Box_t],
) -> Tuple[List[PlacedBox_t], List[str]]:
    """
    Top-left-origin first-fit guillotine layer packing.

    Inputs:
      truck: Truck_t
      boxes: List[Box_t]

    Output:
      (
        placed_boxes: List[PlacedBox_t],
        notes: List[str]
      )

    Side effect:
      modifies the original `boxes` list so that it contains ONLY unplaced boxes.

    Assumptions:
      - Y is the vertical axis.
      - Each layer is packed over the truck floor (X by Z plane).
      - Box floor rotation is Y-axis only:
          (width, depth) or (depth, width)
      - Boxes are sorted by non-increasing height, then footprint, then volume.
      - Each new layer height is the tallest remaining box that starts that layer.
    """
    placed_boxes: List["PlacedBox_t"] = []
    notes: List[str] = []

    if truck.width <= 0 or truck.depth <= 0 or truck.height <= 0:
        notes.append("Truck dimensions must all be positive.")
        return placed_boxes, notes

    if not boxes:
        notes.append("No boxes provided.")
        return placed_boxes, notes

    # Sort in-place-ish, but preserve object identity since we must mutate original list later.
    remaining: List[Box_t] = sorted(
        boxes,
        key=lambda b: (
            -b.height,
            -(b.width * b.depth),
            -(b.width * b.depth * b.height),
            -(b.priority if b.priority is not None else 0.0),
            b.id,
        ),
    )

    current_y = 0.0
    layer_index = 0

    total_weight = 0.0
    if truck.max_weight is not None:
        # We will enforce weight as we accept placements.
        notes.append(f"Truck max weight = {truck.max_weight}")

    while remaining and current_y < truck.height - _EPS:
        # Skip boxes that can never fit in remaining truck height
        remaining_height = truck.height - current_y
        fit_height_candidates = [b for b in remaining if b.height <= remaining_height + _EPS]

        if not fit_height_candidates:
            notes.append(
                f"Stopped: no remaining boxes fit within remaining truck height {remaining_height:.3f}."
            )
            break

        # First-fit-decreasing-by-height style layer choice:
        # layer height is set by the first remaining box that can still fit vertically.
        seed_box = fit_height_candidates[0]
        layer_height = seed_box.height

        layer_candidates: List[Box_t] = [
            b for b in remaining if b.height <= layer_height + _EPS
        ]

        # Filter candidates that can fit truck floor in at least one allowed orientation.
        floor_fit_candidates: List[Box_t] = []
        skipped_floor: List[Box_t] = []

        for b in layer_candidates:
            fits_normal = (b.width <= truck.width + _EPS and b.depth <= truck.depth + _EPS)
            fits_rot = (b.depth <= truck.width + _EPS and b.width <= truck.depth + _EPS)
            if fits_normal or fits_rot:
                floor_fit_candidates.append(b)
            else:
                skipped_floor.append(b)

        if not floor_fit_candidates:
            notes.append(
                f"Layer {layer_index}: no candidate boxes fit on truck floor for layer height {layer_height:.3f}."
            )
            # Remove impossible boxes only if they can never fit any future layer.
            impossible_now = [
                b for b in remaining
                if not (
                    (b.width <= truck.width + _EPS and b.depth <= truck.depth + _EPS) or
                    (b.depth <= truck.width + _EPS and b.width <= truck.depth + _EPS)
                )
            ]
            if impossible_now:
                for b in impossible_now:
                    remaining.remove(b)
                notes.append(
                    f"Removed {len(impossible_now)} box(es) that cannot fit truck floor in any allowed orientation."
                )
            continue

        layer_placements, layer_unplaced, layer_notes = _pack_single_layer_ffg(
            floor_fit_candidates,
            truck.width,
            truck.depth,
        )
        notes.extend([f"Layer {layer_index}: {msg}" for msg in layer_notes])

        if not layer_placements:
            notes.append(f"Layer {layer_index}: nothing placed, stopping to avoid infinite loop.")
            break

        # Commit placements to 3D truck coordinates
        placed_ids = set()
        placed_weight_this_layer = 0.0

        for lp in layer_placements:
            box = lp.box

            if truck.max_weight is not None:
                if total_weight + placed_weight_this_layer + box.weight > truck.max_weight + _EPS:
                    notes.append(
                        f"Skipped box {box.id}: placing it would exceed max truck weight."
                    )
                    continue

            placed_boxes.append(
                PlacedBox_t(
                    id=box.id,
                    x=lp.x,
                    y=current_y,
                    z=lp.z,
                    rotation=lp.rotation,
                )
            )
            placed_ids.add(box.id)
            placed_weight_this_layer += box.weight

        if not placed_ids:
            notes.append(
                f"Layer {layer_index}: candidate placements existed, but all were rejected by weight limit."
            )
            break

        total_weight += placed_weight_this_layer

        # Remove all actually placed boxes from remaining
        remaining = [b for b in remaining if b.id not in placed_ids]

        notes.append(
            f"Layer {layer_index}: placed {len(placed_ids)} box(es) at y={current_y:.3f} with layer height {layer_height:.3f}."
        )

        current_y += layer_height
        layer_index += 1

    # Mutate original list to contain only unplaced boxes
    boxes[:] = remaining

    notes.append(f"Total placed boxes: {len(placed_boxes)}")
    notes.append(f"Total unplaced boxes: {len(boxes)}")
    notes.append(f"Total used height: {current_y:.3f} / {truck.height:.3f}")

    if truck.max_weight is not None:
        notes.append(f"Total placed weight: {total_weight:.3f} / {truck.max_weight:.3f}")

    return placed_boxes, notes