from python.api.schemas import Box, PackingRequest, Truck
from python.vtl_core.domain.models import Box_t, PackRegion, PlacedBox_t, Truck_t
from python.vtl_core.packing.processing import (
    Hstix,
    begin_pack,
    create_instances,
    get_best_heuristic_for_region,
    layer_pack,
)
from python.vtl_core.packing.scoring import ScoringEngine


def make_box(id_: str, w: float, h: float, d: float, weight: float = 1.0, priority: float = 0.0) -> Box_t:
    return Box_t(id=id_, width=w, height=h, depth=d, weight=weight, priority=priority)


def test_scoring_engine_returns_expected_component_scores():
    truck = Truck_t(id='t', width=4.0, height=2.0, depth=4.0)
    original = [
        make_box('a', 2.0, 1.0, 2.0, weight=10.0),
        make_box('b', 2.0, 1.0, 2.0, weight=10.0),
    ]
    placed = [
        PlacedBox_t(id='a', x=0.0, y=0.0, z=0.0, rotation=0),
        PlacedBox_t(id='b', x=2.0, y=1.0, z=2.0, rotation=0),
    ]

    scores = ScoringEngine(truck).get_all_scores(placed, original)

    assert scores['utilization'] == 0.25
    assert scores['stability'] == 0.9
    assert scores['mass_balance'] == 0.5
    assert scores['total_score'] == 0.495


def test_create_instances_maps_pydantic_request_to_internal_models():
    req = PackingRequest(
        truck=Truck(id='t', width=2.0, height=3.0, depth=4.0, max_weight=100.0),
        boxes=[Box(id='b', width=1.0, height=1.0, depth=1.0, weight=5.0, priority=2.0)],
    )

    truck, boxes = create_instances(req)

    assert truck.id == 't'
    assert truck.max_weight == 100.0
    assert len(boxes) == 1
    assert boxes[0].id == 'b'
    assert boxes[0].priority == 2.0


def test_get_best_heuristic_returns_valid_enum_for_simple_region():
    truck = Truck_t(id='t', width=4.0, height=2.0, depth=4.0)
    boxes = [make_box('a1', 1.0, 1.0, 1.0), make_box('a2', 1.0, 1.0, 1.0)]
    region = PackRegion(x=0.0, y=0.0, z=0.0, width=4.0, depth=4.0, height=2.0)

    heuristic = get_best_heuristic_for_region(truck, boxes, region)

    assert heuristic in {Hstix.FFR, Hstix.FFG, Hstix.MAX, Hstix.SKY}


def test_layer_pack_continues_into_additional_regions_and_layers():
    truck = Truck_t(id='t', width=2.0, height=2.0, depth=4.0)
    boxes = [
        make_box('a1', 1.0, 1.0, 1.0),
        make_box('a2', 1.0, 1.0, 1.0),
        make_box('a3', 1.0, 1.0, 1.0),
        make_box('a4', 1.0, 1.0, 1.0),
        make_box('a5', 2.0, 1.0, 1.0),
    ]

    placed, notes = layer_pack(truck=truck, boxes=boxes)

    assert len(placed) >= 4
    assert any('Selected [' in note for note in notes)
    assert len(boxes) < 5


def test_begin_pack_returns_payload_with_expected_shape():
    truck = Truck_t(id='t', width=2.0, height=2.0, depth=2.0)
    boxes = [make_box('a1', 1.0, 1.0, 1.0), make_box('a2', 1.0, 1.0, 1.0)]

    payload = begin_pack(truck, boxes)

    assert set(payload.keys()) >= {'placed', 'unplaced', 'utilization', 'notes', 'runtime_ms'}
    assert len(payload['placed']) == 2
    assert len(payload['unplaced']) == 0
    assert payload['utilization'] > 0
    assert payload['runtime_ms'] >= 0
    assert any('FINAL SCORE' in note for note in payload['notes'])
