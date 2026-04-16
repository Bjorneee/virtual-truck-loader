from typing import List, Tuple, Optional
from enum import Enum, auto
from dataclasses import dataclass

from python.api.schemas import PackingRequest, PlacedBox, Box
from python.vtl_core.domain.models import Truck_t, Box_t, PlacedBox_t

from python.vtl_core.packing.heurisitics import (
    ff_row_pack,
    ff_guillotine_pack,
    maxrects_pack,
    skyline_pack,
)

_EPS = 1e-9


class Hstix(Enum):
    FFR = auto()
    FFG = auto()
    MAX = auto()
    SKY = auto()


def create_instances(req: PackingRequest) -> Tuple[Truck_t, List[Box_t]]:
    truck = Truck_t(
        id=req.truck.id,
        width=req.truck.width,
        height=req.truck.height,
        depth=req.truck.depth,
        max_weight=req.truck.max_weight,
    )

    boxes: List[Box_t] = []
    for box in req.boxes:
        boxes.append(
            Box_t(
                id=box.id,
                width=box.width,
                height=box.height,
                depth=box.depth,
                weight=box.weight,
                priority=box.priority,
            )
        )

    return truck, boxes


def begin_pack(
    truck: Truck_t,
    boxes: List[Box_t],
) -> Tuple[List[PlacedBox], List[Box], float, List[str]]:
    original_load = boxes.copy()

    placed_internal, notes = layer_pack(
        truck=truck,
        boxes=boxes,
    )

    placed = [PlacedBox.model_validate(p_box) for p_box in placed_internal]
    unplaced = [Box.model_validate(box) for box in boxes]
    utilization = get_utilization(truck, placed_internal, original_load)

    return placed, unplaced, utilization, notes


test = Hstix.FFR

@dataclass
class PackRegion:
    x: float
    y: float
    z: float
    width: float
    depth: float
    height: float


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


def layer_pack(
    truck: Truck_t,
    boxes: List[Box_t],
    initial_h: Optional[Hstix] = None
) -> Tuple[List[PlacedBox_t], List[str]]:

    heuristic: Hstix = initial_h or test

    placed: List[PlacedBox_t] = []
    notes: List[str] = []

    # Start with the full original truck as the first region.
    regions: List[PackRegion] = [
        PackRegion(
            x=0.0,
            y=0.0,
            z=0.0,
            width=truck.width,
            depth=truck.depth,
            height=truck.height,
        )
    ]

    layer_index = 0

    while boxes and regions:
        region = regions.pop()

        if region.width <= _EPS or region.depth <= _EPS or region.height <= _EPS:
            continue

        initial_box_count = len(boxes)

        # The next batch type is defined by the first remaining box.
        anchor = boxes[0]

        local_truck = Truck_t(
            id=f"{truck.id}_region_{layer_index}",
            width=region.width,
            depth=region.depth,
            height=region.height,
            max_weight=truck.max_weight,
        )

        match heuristic:
            case Hstix.FFR:
                layer_data = ff_row_pack(
                    truck=local_truck,
                    boxes=boxes,
                    layer_y=region.y,
                )
            case Hstix.FFG:
                layer_data = ff_guillotine_pack(
                    truck=local_truck,
                    boxes=boxes,
                    layer_y=region.y,
                )
            case Hstix.MAX:
                layer_data = maxrects_pack(
                    truck=local_truck,
                    boxes=boxes,
                    layer_y=region.y,
                )
            case Hstix.SKY:
                layer_data = skyline_pack(
                    truck=local_truck,
                    boxes=boxes,
                    layer_y=region.y,
                )
            case _:
                raise ValueError("Invalid heuristic choice.")

        local_placed, layer_notes, used_h, x_cursor, z_cursor = layer_data

        notes.append(
            f"Region {layer_index}: origin=({region.x:.3f}, {region.y:.3f}, {region.z:.3f}) "
            f"size=({region.width:.3f}, {region.depth:.3f}, {region.height:.3f})"
        )
        notes.extend(layer_notes)

        # If nothing was placed here, skip this region and continue with the next one.
        if not local_placed:
            notes.append("No boxes placed in this region.")
            layer_index += 1
            continue

        # Compute local envelope before translating to absolute truck coordinates.
        used_x, used_z = _compute_local_extents(anchor, local_placed)

        # Translate x/z into absolute coordinates of the original truck.
        _translate_placements(local_placed, region.x, region.z)

        placed.extend(local_placed)

        # ---------- Create child regions ----------

        # 1) Above supported rectangle
        remaining_height_above = region.height - used_h
        if used_h > _EPS and x_cursor > _EPS and z_cursor > _EPS and remaining_height_above > _EPS:
            regions.append(
                PackRegion(
                    x=region.x,
                    y=region.y + used_h,
                    z=region.z,
                    width=x_cursor,
                    depth=z_cursor,
                    height=remaining_height_above,
                )
            )

        # 2) Right floor remainder of the used envelope
        remaining_right_width = region.width - used_x
        if remaining_right_width > _EPS:
            regions.append(
                PackRegion(
                    x=region.x + used_x,
                    y=region.y,
                    z=region.z,
                    width=remaining_right_width,
                    depth=region.depth,
                    height=region.height,
                )
            )

        # 3) Back floor remainder of the used envelope
        remaining_back_depth = region.depth - used_z
        if remaining_back_depth > _EPS and used_x > _EPS:
            regions.append(
                PackRegion(
                    x=region.x,
                    y=region.y,
                    z=region.z + used_z,
                    width=used_x,
                    depth=remaining_back_depth,
                    height=region.height,
                )
            )

        if len(boxes) == initial_box_count:
            notes.append("Box list unchanged after placing in region; continuing anyway.")

        layer_index += 1
        heuristic = test  # replace later with optimization choice if needed

    return placed, notes


def get_utilization(
    truck: Truck_t,
    p_boxes: List[PlacedBox_t],
    boxes: List[Box_t],
) -> float:
    box_map = {b.id: b for b in boxes}

    total_volume = 0.0
    for p_box in p_boxes:
        matching = box_map.get(p_box.id)
        if matching is None:
            raise ValueError("Placed box could not be located in original load list.")
        total_volume += matching.volume

    return total_volume / truck.volume