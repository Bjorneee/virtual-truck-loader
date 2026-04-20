import copy
import json
from pathlib import Path
from statistics import mean
from time import perf_counter

from fastapi import FastAPI
from fastapi.testclient import TestClient

from python.api.routes import router

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'evaluation' / 'stress-test-results.md'

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
    return {
        'truck': {'id': 'SmallDense', 'width': 2.4, 'height': 2.6, 'depth': 12.0, 'max_weight': 8000.0},
        'boxes': [
            {'id': f'S{i+1:03d}', 'width': 0.4, 'height': 0.4, 'depth': 0.4, 'weight': 4.0, 'priority': 0.0}
            for i in range(count)
        ],
    }


def mixed_with_oversized_payload(valid_count: int = 80, oversized_count: int = 20) -> dict:
    boxes = [
        {'id': f'V{i+1:03d}', 'width': 0.6, 'height': 0.5, 'depth': 0.5, 'weight': 8.0, 'priority': 0.0}
        for i in range(valid_count)
    ]
    boxes.extend([
        {'id': f'O{i+1:03d}', 'width': 3.0, 'height': 3.0, 'depth': 3.0, 'weight': 20.0, 'priority': 0.0}
        for i in range(oversized_count)
    ])
    return {
        'truck': {'id': 'MixedOversized', 'width': 2.4, 'height': 2.6, 'depth': 10.0, 'max_weight': 8000.0},
        'boxes': boxes,
    }


def multilayer_payload(count: int = 72) -> dict:
    return {
        'truck': {'id': 'MultiLayer', 'width': 2.4, 'height': 2.4, 'depth': 6.0, 'max_weight': 5000.0},
        'boxes': [
            {'id': f'M{i+1:03d}', 'width': 0.6, 'height': 0.4, 'depth': 0.6, 'weight': 5.0, 'priority': 0.0}
            for i in range(count)
        ],
    }


def validate(payload, data):
    total = len(payload['boxes'])
    placed = data.get('placed') or []
    unplaced = data.get('unplaced') or []
    ok = True
    checks = []
    checks.append((len(placed) + len(unplaced) == total, 'placed + unplaced == total input'))
    checks.append((len({p['id'] for p in placed}) == len(placed), 'placed ids unique'))
    checks.append((len({u['id'] for u in unplaced}) == len(unplaced), 'unplaced ids unique'))
    checks.append((not ({p['id'] for p in placed} & {u['id'] for u in unplaced}), 'placed/unplaced ids disjoint'))
    checks.append((0.0 <= data['utilization'] <= 1.0, 'utilization in [0,1]'))
    checks.append((data['runtime_ms'] >= 0.0, 'runtime_ms non-negative'))
    box_map = {b['id']: b for b in payload['boxes']}
    truck = payload['truck']
    bounds_ok = True
    for pb in placed:
        box = box_map[pb['id']]
        w, d = (box['depth'], box['width']) if pb.get('rotation', 0) == 1 else (box['width'], box['depth'])
        if not (
            pb['x'] >= -1e-9 and pb['y'] >= -1e-9 and pb['z'] >= -1e-9 and
            pb['x'] + w <= truck['width'] + 1e-6 and
            pb['y'] + box['height'] <= truck['height'] + 1e-6 and
            pb['z'] + d <= truck['depth'] + 1e-6
        ):
            bounds_ok = False
            break
    checks.append((bounds_ok, 'placed boxes remain within truck bounds'))
    for passed, _ in checks:
        ok = ok and passed
    return ok, checks


scenarios = [
    ('dense-small-180', small_box_payload(180), 'High item count using identical small cubes to stress region growth and repeated layer creation.'),
    ('warehouse-x5', with_suffix(load_payload('3_warehouse.json'), 5), 'Realistic mixed warehouse load repeated five times to stress dynamic heuristic selection.'),
    ('fragmentation-x4', with_suffix(load_payload('11_fragmentation.json'), 4), 'Amplified fragmentation scenario to stress support rectangle and sub-region reuse.'),
    ('mixed-oversized', mixed_with_oversized_payload(80, 20), 'Large mixed load with intentionally impossible boxes to stress negative-path handling.'),
    ('multilayer-72', multilayer_payload(72), 'Uniform stackable boxes sized to force multiple Y-levels in the same truck.'),
]

rows = []
sections = []
for name, payload, description in scenarios:
    wall = []
    reported = []
    placed_counts = []
    unplaced_counts = []
    utilizations = []
    last_data = None
    for _ in range(3):
        t0 = perf_counter()
        response = client.post('/pack', json=payload)
        elapsed = (perf_counter() - t0) * 1000
        data = response.json()
        wall.append(elapsed)
        reported.append(data['runtime_ms'])
        placed_counts.append(len(data.get('placed') or []))
        unplaced_counts.append(len(data.get('unplaced') or []))
        utilizations.append(data['utilization'])
        last_data = data
    ok, checks = validate(payload, last_data)
    rows.append((
        name,
        len(payload['boxes']),
        int(round(mean(placed_counts))),
        int(round(mean(unplaced_counts))),
        mean(reported),
        mean(wall),
        mean(utilizations),
        'PASS' if ok else 'FAIL',
    ))
    check_lines = "\n".join([f"- [{'x' if p else ' '}] {desc}" for p, desc in checks])
    note_preview = "\n".join(f"  - {n}" for n in (last_data.get('notes') or [])[:6])
    sections.append(
        f"## {name}\n\n{description}\n\n"
        f"- Input boxes: {len(payload['boxes'])}\n"
        f"- Mean placed over 3 runs: {mean(placed_counts):.2f}\n"
        f"- Mean unplaced over 3 runs: {mean(unplaced_counts):.2f}\n"
        f"- Mean reported runtime (ms): {mean(reported):.2f}\n"
        f"- Mean wall runtime (ms): {mean(wall):.2f}\n"
        f"- Mean utilization: {mean(utilizations):.4f}\n"
        f"- Final status: {'PASS' if ok else 'FAIL'}\n\n"
        f"Validation checks:\n{check_lines}\n\n"
        f"Notes preview:\n{note_preview}\n"
    )

header = (
    '# Stress Test Results\n\n'
    'Generated by `tests/run_stress_tests.py` against the current FastAPI packing pipeline. '
    'Each scenario was executed 3 times and summarized by mean values.\n\n'
)

table = (
    '| Scenario | Input Boxes | Mean Placed | Mean Unplaced | Mean Reported Runtime (ms) | '
    'Mean Wall Runtime (ms) | Mean Utilization | Status |\n'
    '|---|---:|---:|---:|---:|---:|---:|---|\n'
)
for r in rows:
    table += f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]:.2f} | {r[5]:.2f} | {r[6]:.4f} | {r[7]} |\n"

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(header + table + '\n' + '\n'.join(sections), encoding='utf-8')
print(f'Wrote {OUT}')
