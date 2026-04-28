from python.vtl_core.domain.models import Box_t, PlacedBox_t, Truck_t
from python.vtl_core.utils import (
    _compute_local_extents,
    _height_cap,
    _largest_complete_top_left_rectangle,
    _split_same_type_prefix,
    _translate_placements,
)


def make_box(id_: str, w: float, h: float, d: float, weight: float = 1.0, priority: float = 0.0) -> Box_t:
    return Box_t(id=id_, width=w, height=h, depth=d, weight=weight, priority=priority)


def test_box_equality_uses_dimensions_only():
    a = make_box('a', 1.0, 2.0, 3.0, weight=10.0, priority=1.0)
    b = make_box('b', 1.0, 2.0, 3.0, weight=99.0, priority=9.0)
    c = make_box('c', 1.0, 2.0, 4.0)

    assert a == b
    assert a != c


def test_box_volume_and_footprint_properties():
    box = make_box('x', 2.0, 3.0, 4.0)
    truck = Truck_t(id='t', width=2.0, height=3.0, depth=5.0)

    assert box.volume == 24.0
    assert box.footprint == 8.0
    assert truck.volume == 30.0
    assert truck.floor_area == 10.0


def test_split_same_type_prefix_stops_at_first_different_type_and_sorts_within_batch():
    first = make_box('zeta', 1.0, 1.0, 1.0, priority=0.0)
    second = make_box('alpha', 1.0, 1.0, 1.0, priority=10.0)
    third = make_box('other', 2.0, 1.0, 1.0)
    boxes = [first, second, third]

    batch, remainder, anchor = _split_same_type_prefix(boxes, sort_boxes=True)

    assert anchor == first
    assert [b.id for b in batch] == ['alpha', 'zeta']
    assert [b.id for b in remainder] == ['other']


def test_height_cap_handles_invalid_truck_and_explicit_layer_cap():
    invalid_truck = Truck_t(id='bad', width=0.0, height=2.0, depth=3.0)
    truck = Truck_t(id='ok', width=2.0, height=5.0, depth=3.0)

    assert _height_cap(invalid_truck, None) == 0.0
    assert _height_cap(truck, None) == 5.0
    assert _height_cap(truck, 2.5) == 2.5
    assert _height_cap(truck, 10.0) == 5.0


def test_translate_and_compute_local_extents_respect_rotation():
    anchor = make_box('a', 2.0, 1.0, 3.0)
    placed = [
        PlacedBox_t(id='a1', x=0.0, y=0.0, z=0.0, rotation=0),
        PlacedBox_t(id='a2', x=2.0, y=0.0, z=0.0, rotation=1),
    ]

    used_x, used_z = _compute_local_extents(anchor, placed)
    assert used_x == 5.0
    assert used_z == 3.0

    _translate_placements(placed, 10.0, 20.0)
    assert (placed[0].x, placed[0].z) == (10.0, 20.0)
    assert (placed[1].x, placed[1].z) == (12.0, 20.0)


def test_largest_complete_top_left_rectangle_detects_gaps():
    complete_rect = _largest_complete_top_left_rectangle(
        placed_rects=[(0.0, 0.0, 1.0, 1.0), (1.0, 0.0, 1.0, 1.0)],
        truck_width=2.0,
        truck_depth=1.0,
    )
    gap_rect = _largest_complete_top_left_rectangle(
        placed_rects=[(0.0, 0.0, 1.0, 1.0), (2.0, 0.0, 1.0, 1.0)],
        truck_width=3.0,
        truck_depth=1.0,
    )

    assert complete_rect == (2.0, 1.0)
    assert gap_rect == (1.0, 1.0)
