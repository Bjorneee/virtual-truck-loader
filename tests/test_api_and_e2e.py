from fastapi.testclient import TestClient

from python.api.main import app
from python.api.schemas import PackingRequest
from python.services.packing_services import run_packing


client = TestClient(app)


def test_root_and_health_endpoints_work():
    root = client.get('/')
    health = client.get('/health')

    assert root.status_code == 200
    assert root.json() == {'Hello': 'World'}
    assert health.status_code == 200
    assert health.json() == {'status': 'ok'}


def test_pack_endpoint_accepts_real_payload_and_returns_consistent_counts(many_payload):
    response = client.post('/pack', json=many_payload)

    assert response.status_code == 200
    data = response.json()
    assert len(data['placed']) + len(data['unplaced']) == len(many_payload['boxes'])
    assert data['runtime_ms'] >= 0
    assert isinstance(data['utilization'], float)
    assert any('FINAL SCORE' in note for note in data['notes'])


def test_pack_endpoint_rejects_invalid_payload_shape():
    response = client.post('/pack', json={'truck': {'id': 't'}, 'boxes': []})

    assert response.status_code == 422


def test_service_run_packing_sorts_and_processes_realistic_warehouse_payload(warehouse_payload):
    req = PackingRequest.model_validate(warehouse_payload)

    result = run_packing(req)

    assert len(result.placed) + len(result.unplaced) == len(req.boxes)
    assert result.runtime_ms >= 0
    assert result.utilization >= 0
    assert any('REGIONAL DYNAMIC SELECTION ACTIVE' in note for note in result.notes)


def test_fragmentation_payload_does_not_crash_and_places_something(fragmentation_payload):
    response = client.post('/pack', json=fragmentation_payload)

    assert response.status_code == 200
    data = response.json()
    assert len(data['placed']) > 0
    assert len(data['placed']) + len(data['unplaced']) == len(fragmentation_payload['boxes'])
