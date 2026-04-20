from python.vtl_core.domain.models import Box_t, Truck_t
from python.vtl_core.packing.heurisitics import (
    ff_guillotine_pack,
    ff_row_pack,
    maxrects_pack,
    skyline_pack,
)


HEURISTICS = [ff_row_pack, ff_guillotine_pack, maxrects_pack, skyline_pack]


def make_box(id_: str, w: float, h: float, d: float, weight: float = 1.0, priority: float = 0.0) -> Box_t:
    return Box_t(id=id_, width=w, height=h, depth=d, weight=weight, priority=priority)


def test_all_heuristics_only_process_one_box_type_prefix():
    truck = Truck_t(id='t', width=4.0, height=2.0, depth=4.0)

    for heuristic in HEURISTICS:
        boxes = [
            make_box('a1', 1.0, 1.0, 1.0),
            make_box('a2', 1.0, 1.0, 1.0),
            make_box('b1', 2.0, 1.0, 1.0),
        ]
        placed, notes, used_h, x_cursor, z_cursor = heuristic(truck=truck, boxes=boxes)

        assert len(placed) == 2
        assert [b.id for b in boxes] == ['b1']
        assert used_h == 1.0
        assert x_cursor > 0.0 and z_cursor > 0.0
        assert any('Packed by:' in note for note in notes)


def test_all_heuristics_reject_boxes_over_height_cap_and_keep_failures():
    truck = Truck_t(id='t', width=4.0, height=5.0, depth=4.0)

    for heuristic in HEURISTICS:
        boxes = [make_box('too_tall', 1.0, 3.0, 1.0)]
        placed, notes, used_h, _, _ = heuristic(truck=truck, boxes=boxes, layer_height=2.0)

        assert len(placed) == 0
        assert [b.id for b in boxes] == ['too_tall']
        assert used_h == 0.0
        assert any('exceeds height cap' in note for note in notes)


def test_ff_row_pack_starts_new_row_when_needed():
    truck = Truck_t(id='t', width=2.0, height=3.0, depth=2.0)
    boxes = [
        make_box('a1', 1.0, 1.0, 1.0),
        make_box('a2', 1.0, 1.0, 1.0),
        make_box('a3', 1.0, 1.0, 1.0),
    ]

    placed, _, _, x_cursor, z_cursor = ff_row_pack(truck=truck, boxes=boxes)

    assert [(p.x, p.z) for p in placed] == [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]
    assert (x_cursor, z_cursor) == (2.0, 1.0)


def test_ff_guillotine_pack_rotates_when_required():
    truck = Truck_t(id='t', width=2.0, height=2.0, depth=3.0)
    boxes = [make_box('rot', 3.0, 1.0, 2.0)]

    placed, _, _, _, _ = ff_guillotine_pack(truck=truck, boxes=boxes)

    assert len(placed) == 1
    assert placed[0].rotation == 1


def test_maxrects_and_skyline_can_place_multiple_same_type_boxes_without_losing_remainder():
    truck = Truck_t(id='t', width=3.0, height=2.0, depth=2.0)

    for heuristic in (maxrects_pack, skyline_pack):
        boxes = [
            make_box('a1', 1.0, 1.0, 1.0),
            make_box('a2', 1.0, 1.0, 1.0),
            make_box('a3', 1.0, 1.0, 1.0),
            make_box('a4', 1.0, 1.0, 1.0),
        ]
        placed, _, _, _, _ = heuristic(truck=truck, boxes=boxes)

        assert len(placed) == 4
        assert boxes == []
