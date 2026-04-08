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

from python.vtl_core.domain.models import Box_t, PlacedBox_t, Truck_t


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


def first_fit_pack(truck: Truck_t, boxes: List[Box_t]) -> Tuple[List[PlacedBox_t], List[str]]:
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
    Top-left-origin free rectangle in a single 2D layer.

    Layer coordinates:
      - origin is top-left
      - x increases to the right
      - z increases downward / forward

    Rectangle spans:
      x in [x, x + w)
      z in [z, z + d)
    """
    x: float
    z: float
    w: float
    d: float


_EPS = 0


def _fits(w: float, d: float, rect: FreeRectTL) -> bool:
    return w <= rect.w + _EPS and d <= rect.d + _EPS


def _prune_free_rects(rects: List[FreeRectTL]) -> List[FreeRectTL]:
    """
    Remove degenerate rectangles and rectangles fully contained in others.
    """
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


def _split_free_rect_top_left(
    rect: FreeRectTL,
    placed_w: float,
    placed_d: float,
) -> List[FreeRectTL]:
    """
    Guillotine split after placing a box at the TOP-LEFT corner of rect.

    Produces:
      - right remainder
      - bottom remainder
    """
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


def _choose_orientation(box: Box_t, rect: FreeRectTL) -> Optional[Tuple[float, float, int]]:
    """
    Allowed orientations for a layer:
      rotation 0: (width, depth)
      rotation 1: (depth, width)  -> Y-axis rotation

    Returns:
      (placed_width, placed_depth, rotation_code)
    """
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


def ff_guillotine_pack(
    truck: Truck_t,
    boxes: List[Box_t],
    layer_y: float = 0.0,
    layer_height: Optional[float] = None,
    sort_boxes: bool = True,
) -> Tuple[List[PlacedBox_t], List[str], float]:
    """
    Pack exactly ONE layer using a top-left-origin first-fit guillotine heuristic.

    Inputs:
      truck        : Truck_t
      boxes        : List[Box_t]
      layer_y      : y-position of the bottom of this layer
      layer_height : if provided, only boxes with height <= layer_height are eligible
                     if omitted, the layer height is chosen as the tallest remaining
                     box that still fits vertically
      sort_boxes   : if True, packs in non-increasing height / footprint / volume order

    Returns:
      (
        placed_boxes: List[PlacedBox_t],
        notes: List[str]
        layer_height: float
      )

    Side effect:
      modifies the input `boxes` list in place so that it contains only boxes
      that were NOT placed in this layer.
    """
    notes: List[str] = []
    placed: List[PlacedBox_t] = []

    if not boxes:
        notes.append("No boxes provided.")
        return placed, notes

    if truck.width <= 0 or truck.depth <= 0 or truck.height <= 0:
        notes.append("Truck dimensions must be positive.")
        return placed, notes

    if layer_y < 0 or layer_y >= truck.height:
        notes.append(f"Invalid layer_y={layer_y}. Must satisfy 0 <= layer_y < truck.height.")
        return placed, notes

    remaining_vertical_space = truck.height - layer_y
    if remaining_vertical_space <= _EPS:
        notes.append("No remaining vertical space for this layer.")
        return placed, notes

    candidates = list(boxes)
    
    if sort_boxes:
        candidates.sort(
            key=lambda b: (
                -b.height,
                -(b.width * b.depth),
                -(b.width * b.depth * b.height),
                -(b.priority if b.priority is not None else 0.0),
                b.id,
            )
        )

    # Determine layer height if not supplied
    if layer_height is None:
        seed = next((b for b in candidates if b.height <= remaining_vertical_space + _EPS), None)
        if seed is None:
            notes.append(
                f"No boxes fit vertically in remaining height {remaining_vertical_space:.3f}."
            )
            return placed, notes
        layer_height = seed.height

    if layer_height <= 0:
        notes.append("layer_height must be positive.")
        return placed, notes

    if layer_height > remaining_vertical_space + _EPS:
        notes.append(
            f"Layer height {layer_height:.3f} exceeds remaining vertical space {remaining_vertical_space:.3f}."
        )
        return placed, notes

    # Only boxes that fit the layer height are eligible
    eligible: List[Box_t] = [b for b in candidates if b.height <= layer_height + _EPS]
    if not eligible:
        notes.append(f"No boxes eligible for layer height {layer_height:.3f}.")
        return placed, notes

    free_rects: List[FreeRectTL] = [FreeRectTL(0.0, 0.0, truck.width, truck.depth)]
    placed_ids: set[str] = set()

    for box in eligible:
        placed_this_box = False

        for i, rect in enumerate(free_rects):
            orient = _choose_orientation(box, rect)
            if orient is None:
                continue

            pw, pd, rot = orient

            # Place at top-left corner of this free rectangle
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
            placed_ids.add(box.id)

            # Replace used free rectangle with guillotine split results
            new_rects = free_rects[:i] + free_rects[i + 1:]
            new_rects.extend(_split_free_rect_top_left(rect, pw, pd))
            free_rects = _prune_free_rects(new_rects)

            placed_this_box = True
            break

        if not placed_this_box:
            continue

    # Mutate original list to only unplaced boxes
    boxes[:] = [b for b in boxes if b.id not in placed_ids]

    used_area = 0.0
    for pb in placed:
        # Find the original box by id from eligible
        box = next(b for b in eligible if b.id == pb.id)
        used_area += box.width * box.depth

    notes.append(f"Packed one layer at y={layer_y:.3f}.")
    notes.append(f"Layer height used: {layer_height:.3f}")
    notes.append(f"Placed boxes in layer: {len(placed)}")
    notes.append(f"Unplaced boxes remaining: {len(boxes)}")
    notes.append(f"Layer floor utilization: {used_area / (truck.width * truck.depth):.2%}")

    return placed, notes, layer_height