from __future__ import annotations

from typing import List, Optional, Tuple

from python.vtl_core.domain.models import Box_t, PlacedBox_t, Truck_t
from python.vtl_core.domain.models import FreeRectTL, SkylineSeg

from python.vtl_core.utils import _ffg_prune_free_rects, _ffg_split_free_rect, _choose_orientation
from python.vtl_core.utils import _find_best_position_for_box_tl, _rects_intersect, _mr_split_free_rect, _mr_prune_free_rects
from python.vtl_core.utils import _skyline_find_position, _skyline_add_level, _skyline_merge

_EPS = 1e-9


"""                          << FIRST FIT >>
    Single-layer first-fit row packing.

    Packs boxes into exactly one layer starting at y = layer_y.
    Boxes are placed left-to-right along x, and new rows are opened along z.

    Args:
        truck: Truck/container dimensions.
        boxes: Mutable list of boxes. Will be modified in place to contain
               only boxes not placed in this layer.
        layer_y: Bottom y-coordinate of the layer.
        layer_height: Optional maximum allowed box height for this layer.
                      If None, any box that fits in the remaining truck height
                      may be considered.
        sort_boxes: If True, sort candidates before packing.

    Returns:
        placed: List of placed boxes for this layer.
        notes: Informational notes.
        used_layer_height: Max height of any box placed in this layer, or 0.0
                           if nothing was placed.
"""
def ff_row_pack(
    truck: Truck_t,
    boxes: List[Box_t],
    layer_y: float = 0.0,
    layer_height: Optional[float] = None,
    sort_boxes: bool = True,
) -> Tuple[List[PlacedBox_t], List[str], float]:

    placed: List[PlacedBox_t] = []
    notes: List[str] = []

    # Remaining vertical space in truck from this layer upward
    remaining_height = truck.height - layer_y
    if remaining_height <= 0:
        notes.append(f"Layer start y={layer_y} is outside truck height.")
        return placed, notes, 0.0

    # Effective height cap for this layer
    height_cap = remaining_height if layer_height is None else min(layer_height, remaining_height)

    # Work on a copy so we can rebuild boxes[:] with only unplaced boxes later
    candidates = list(boxes)

    if sort_boxes:
        candidates.sort(
            key=lambda b: (
                -b.height,
                -b.footprint,
                -b.volume,
                -(b.priority if b.priority is not None else 0.0),
                b.id,
            )
        )

    unplaced: List[Box_t] = []
    used_layer_height = 0.0

    # Row state
    row_z = 0.0           # z start of current row
    row_depth = 0.0       # max depth used by current row
    row_x = 0.0           # x cursor within current row
    has_row = False

    for box in candidates:

        # Hard reject for this specific layer / truck
        if box.width > truck.width or box.depth > truck.depth:
            unplaced.append(box)
            print(f"Box: [{box.id}] footprint does not fit in truck floor.")
            continue

        if box.height > height_cap:
            unplaced.append(box)
            print(f"Box: [{box.id}] exceeds maximum height.")
            continue

        # First box starts first row
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
            print(f"Box placed: [{box.id}]")
            continue

        # Try to fit in current row
        if row_x + box.width <= truck.width and box.depth <= row_depth:
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
            print(f"Box: [{box.id}] at ({row_x}, {layer_y}, {row_z})")
            continue

        # Otherwise try to open a new row
        new_row_z = row_z + row_depth
        if new_row_z + box.depth <= truck.depth:
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
            print(f"Box: [{box.id}] at (0, {layer_y}, {new_row_z})")
            continue

        # Could not place in this layer
        unplaced.append(box)
        print(f"Box: [{box.id}] could not be placed.")

    boxes[:] = unplaced
    notes.append("Packed by: FFR")

    return placed, notes, used_layer_height



"""                         << First-Fit Guillotine >>

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
def ff_guillotine_pack(
    truck: Truck_t,
    boxes: List[Box_t],
    layer_y: float = 0.0,
    layer_height: Optional[float] = None,
    sort_boxes: bool = True,
) -> Tuple[List[PlacedBox_t], List[str], float]:

    notes: List[str] = []
    placed: List[PlacedBox_t] = []

    if not boxes:
        raise ValueError(f"No boxes provided.")

    if truck.width <= 0 or truck.depth <= 0 or truck.height <= 0:
        raise ValueError(f"Truck dimensions must be positive.")

    if layer_y < 0 or layer_y >= truck.height:
        raise ValueError(f"Invalid layer_y={layer_y}. Must satisfy 0 <= layer_y < truck.height.")

    remaining_vertical_space = truck.height - layer_y
    if remaining_vertical_space <= _EPS:
        print("No remaining vertical space for this layer.")
        return placed, notes

    candidates = list(boxes)
    
    if sort_boxes:
        candidates.sort(
            key=lambda b: (
                -b.height,
                -b.footprint,
                -b.volume,
                -(b.priority if b.priority is not None else 0.0),
                b.id,
            )
        )

    # Determine layer height if not supplied
    if layer_height is None:
        seed = next((b for b in candidates if b.height <= remaining_vertical_space + _EPS), None)
        if seed is None:
            print(
                f"No boxes fit vertically in remaining height {remaining_vertical_space:.3f}."
            )
            return placed, notes
        layer_height = seed.height

    if layer_height <= 0:
        raise ValueError(f"layer_height must be positive.")

    if layer_height > remaining_vertical_space + _EPS:
        raise ValueError(
            f"Layer height {layer_height:.3f} exceeds remaining vertical space {remaining_vertical_space:.3f}."
        )

    # Only boxes that fit the layer height are eligible
    eligible: List[Box_t] = [b for b in candidates if b.height <= layer_height + _EPS]
    if not eligible:
        raise ValueError(f"No boxes eligible for layer height {layer_height:.3f}.")

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
            new_rects.extend(_ffg_split_free_rect(rect, pw, pd))
            free_rects = _ffg_prune_free_rects(new_rects)

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

    print(f"Packed layer at y={layer_y:.3f}.")
    print(f"Layer height used: {layer_height:.3f}")
    print(f"Placed boxes in layer: {len(placed)}")
    print(f"Unplaced boxes remaining: {len(boxes)}")
    print(f"Layer floor utilization: {used_area / (truck.width * truck.depth):.2%}")

    notes.append("Packed by: FFG")

    return placed, notes, layer_height


"""                             << MaxRects >>

    Pack a single floor layer using a top-left-origin MaxRects heuristic.

    Inputs:
      - truck: Truck_t
      - boxes: List[Box_t]
          This list is modified in-place so that, on return, it contains only unplaced boxes.

    Returns:
      - placed: List[PlacedBox_t]
      - notes: List[str]
      - layer_height: float

    Behavior:
      - Single layer only: all placed boxes get y = 0.0
      - Top-left origin on floor plane:
            x = left -> right
            z = top -> bottom
      - Only Y-axis rotation is used for packing footprint:
            (width, depth) <-> (depth, width)
        Height is unchanged.
      - Boxes taller than truck.height are skipped.
      - Boxes wider/deeper than truck floor in both orientations are skipped.

    Heuristic:
      - MaxRects using "Best Area Fit", then "Best Short Side Fit" as tie-breaker.

"""
def maxrects_pack(
    truck: "Truck_t",
    boxes: List["Box_t"],
    layer_y: float = 0.0,
    allow_y_rotation: bool = True,
    sort_boxes: bool = True,
) -> Tuple[List[PlacedBox_t], List[str], float]:

    placed: List[PlacedBox_t] = []
    notes: List[str] = []

    if not boxes:
        raise ValueError(f"No boxes provided.")

    # Start with the full truck floor as one free rectangle.
    free_rects: List[FreeRectTL] = [FreeRectTL(0.0, 0.0, truck.width, truck.depth)]

    # Work on candidates, but mutate original list only at the end.
    candidates = list(boxes)

    if sort_boxes:
        # Tallest first, then largest footprint, then largest volume, then priority, then id.
        candidates.sort(
            key=lambda b: (
                -b.height,
                -b.footprint,
                -b.volume,
                -(b.priority if b.priority is not None else 0.0),
                b.id,
            )
        )

    unplaced: List["Box_t"] = []
    layer_height: float = 0.0

    for box in candidates:
        # Height must fit in this single layer.
        if box.height > truck.height + _EPS:
            unplaced.append(box)
            print(
                f"Box {box.id} skipped: height {box.height} exceeds truck height {truck.height}."
            )
            continue

        placement = _find_best_position_for_box_tl(
            box=box,
            free_rects=free_rects,
            allow_y_rotation=allow_y_rotation,
        )

        if placement is None:
            unplaced.append(box)
            print(f"Box {box.id} could not be placed in this layer.")
            continue

        rect_index, px, pz, pw, pd, rotation = placement
        used_rect = free_rects[rect_index]

        # Record placed box.
        placed.append(
            PlacedBox_t(
                id=box.id,
                x=px,
                y=layer_y,
                z=pz,
                rotation=rotation,
            )
        )

        # Update resulting layer height.
        if box.height > layer_height:
            layer_height = box.height

        # Split all intersecting free rectangles around the placed footprint.
        new_free_rects: List[FreeRectTL] = []
        placed_rect = FreeRectTL(px, pz, pw, pd)

        for fr in free_rects:
            if not _rects_intersect(fr, placed_rect):
                new_free_rects.append(fr)
                continue

            split_parts = _mr_split_free_rect(fr, placed_rect)
            new_free_rects.extend(split_parts)

        free_rects = _mr_prune_free_rects(new_free_rects)

    # Mutate original input list so it contains only unplaced boxes.
    boxes[:] = unplaced

    if placed:
        print(
            f"Packed {len(placed)} box(es) into one layer. Layer height = {layer_height}."
        )
    else:
        print("No boxes were placed in the layer.")

    notes.append("Packed by: MAX")

    return placed, notes, layer_height


"""                         << Skyline Sort >>

    Single-layer skyline packing using top-left-origin floor coordinates.

    Inputs:
      - truck: Truck_t
      - boxes: List[Box_t]
          Mutated in-place so only unplaced boxes remain after packing.
      - layer_y: y-coordinate of the layer base
      - layer_height: optional fixed layer height constraint
      - sort_boxes: whether to sort candidates before packing

    Returns:
      - placed: List[PlacedBox_t]
      - notes: List[str]
      - used_layer_height: float

    Coordinate convention:
      - x increases left -> right
      - z increases top -> bottom
      - y is vertical
      - all placements are top-left origin on the truck floor plane

"""
def skyline_pack(
    truck: Truck_t,
    boxes: List[Box_t],
    layer_y: float = 0.0,
    layer_height: Optional[float] = None,
    sort_boxes: bool = True,
) -> Tuple[List[PlacedBox_t], List[str], float]:

    placed: List[PlacedBox_t] = []
    notes: List[str] = []

    if truck.width <= 0 or truck.depth <= 0 or truck.height <= 0:
        raise ValueError(f"Truck dimensions must be positive.")

    available_height = truck.height - layer_y
    if available_height <= 0:
        raise ValueError(f"Layer base is above truck height.")

    max_layer_height = layer_height if layer_height is not None else available_height
    max_layer_height = min(max_layer_height, available_height)

    if max_layer_height <= 0:
        raise ValueError(f"Layer height must be positive.")

    candidates = list(boxes)

    if sort_boxes:
        candidates.sort(
            key=lambda b: (
                -b.height,
                -b.footprint,
                -b.volume,
                -(b.priority if b.priority is not None else 0.0),
                b.id,
            )
        )

    skyline: List[SkylineSeg] = [SkylineSeg(0.0, 0.0, truck.width)]
    unplaced: List[Box_t] = []
    used_layer_height = 0.0

    for box in candidates:
        if box.height > max_layer_height:
            unplaced.append(box)
            print(
                f"Box {box.id} skipped: height {box.height} exceeds layer height {max_layer_height}."
            )
            continue

        best = _skyline_find_position(skyline, box, truck.depth)

        if best is None:
            unplaced.append(box)
            print(f"Box {box.id} could not be placed in this layer.")
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

        if rotation == 1:
            print(f"Placed {box.id} at ({px}, {layer_y}, {pz}) with Y-rotation.")
        else:
            print(f"Placed {box.id} at ({px}, {layer_y}, {pz}).")

    boxes[:] = unplaced

    if placed:
        print(
            f"Packed {len(placed)} box(es) into skyline layer. Layer height used = {used_layer_height}."
        )
    else:
        print("No boxes were placed in the skyline layer.")

    notes.append("Packed by: SKY")

    return placed, notes, used_layer_height

