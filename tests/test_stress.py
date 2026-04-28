
import copy
import json
from pathlib import Path
from time import perf_counter

from fastapi import FastAPI
from fastapi.testclient import TestClient

from python.api.routes import router

ROOT = Path(__file__).resolve().parents[1]

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def load_payload(name: str) -> dict:
    return json.loads((ROOT / 'tests' / name).read_text())


def with_suffix(payload: dict, repeat: int) -> dict:
    out = copy.deepcopy(payload)
    boxes = []
    for i in range(repeat):
        for box in payload['boxes']:
            clone = copy.deepcopy(box)
            clone['id'] = f"{box['id']}_R{i+1}"
            boxes.append(clone)
    out['boxes'] = boxes
    return out


def small_box_payload(count: int = 180) -> dict:
    payload = {
        'truck': {'id': 'SmallDense', 'width': 2.4, 'height': 2.6, 'depth': 12.0, 'max_weight': 8000.0},
        'boxes': []
    }
    for i in range(count):
        payload['boxes'].append({
            'id': f'S{i+1:03d}',
            'width': 0.4,
            'height': 0.4,
            'depth': 0.4,
            'weight': 4.0,
            'priority': 0.0,
        })
    return payload


def mixed_with_oversized_payload(valid_count: int = 80, oversized_count: int = 20) -> dict:
    payload = {
        'truck': {'id': 'MixedOversized', 'width': 2.4, 'height': 2.6, 'depth': 10.0, 'max_weight': 8000.0},
        'boxes': []
    }
    for i in range(valid_count):
        payload['boxes'].append({
            'id': f'V{i+1:03d}',
            'width': 0.6,
            'height': 0.5,
            'depth': 0.5,
            'weight': 8.0,
            'priority': 0.0,
        })
    for i in range(oversized_count):
        payload['boxes'].append({
            'id': f'O{i+1:03d}',
            'width': 3.0,
            'height': 3.0,
            'depth': 3.0,
            'weight': 20.0,
            'priority': 0.0,
        })
    return payload


def multilayer_payload(count: int = 72) -> dict:
    payload = {
        'truck': {'id': 'MultiLayer', 'width': 2.4, 'height': 2.4, 'depth': 6.0, 'max_weight': 5000.0},
        'boxes': []
    }
    for i in range(count):
        payload['boxes'].append({
            'id': f'M{i+1:03d}',
            'width': 0.6,
            'height': 0.4,
            'depth': 0.6,
            'weight': 5.0,
            'priority': 0.0,
        })
    return payload


def assert_response_integrity(payload: dict, data: dict):
    total = len(payload['boxes'])
    placed = data.get('placed') or []
    unplaced = data.get('unplaced') or []

    assert len(placed) + len(unplaced) == total
    assert len({p['id'] for p in placed}) == len(placed)
    assert len({u['id'] for u in unplaced}) == len(unplaced)
    assert not ({p['id'] for p in placed} & {u['id'] for u in unplaced})
    assert 0.0 <= data['utilization'] <= 1.0
    assert data['runtime_ms'] >= 0.0
    assert isinstance(data['notes'], list)

    box_map = {b['id']: b for b in payload['boxes']}
    truck = payload['truck']
    for pb in placed:
        box = box_map[pb['id']]
        w, d = (box['depth'], box['width']) if pb.get('rotation', 0) == 1 else (box['width'], box['depth'])
        assert pb['x'] >= -1e-9
        assert pb['y'] >= -1e-9
        assert pb['z'] >= -1e-9
        assert pb['x'] + w <= truck['width'] + 1e-6
        assert pb['y'] + box['height'] <= truck['height'] + 1e-6
        assert pb['z'] + d <= truck['depth'] + 1e-6


def exercise_payload(payload: dict):
    t0 = perf_counter()
    response = client.post('/pack', json=payload)
    wall_ms = (perf_counter() - t0) * 1000
    assert response.status_code == 200, response.text
    data = response.json()
    assert_response_integrity(payload, data)
    return data, wall_ms


def test_stress_dense_small_boxes():
    payload = small_box_payload(1000)
    data, wall_ms = exercise_payload(payload)
    assert len(data['placed']) > 0
    assert wall_ms < 30000


def test_stress_warehouse_repeated():
    payload = with_suffix(load_payload('3_warehouse.json'), 50)
    data, wall_ms = exercise_payload(payload)
    assert len(data['placed']) > 0
    assert wall_ms < 30000


def test_stress_fragmentation_repeated():
    payload = with_suffix(load_payload('11_fragmentation.json'), 50)
    data, wall_ms = exercise_payload(payload)
    assert len(data['placed']) > 0
    assert wall_ms < 30000


def test_stress_mixed_with_oversized_boxes():
    payload = mixed_with_oversized_payload(800, 200)
    data, wall_ms = exercise_payload(payload)
    assert len(data['unplaced']) >= 20
    assert wall_ms < 30000


def test_stress_multilayer_same_type_stack():
    payload = multilayer_payload(100)
    data, wall_ms = exercise_payload(payload)
    ys = sorted({round(p['y'], 6) for p in data['placed']})
    assert len(data['placed']) > 0
    assert len(ys) >= 2
    assert wall_ms < 30000
