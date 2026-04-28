from fastapi.testclient import TestClient
from python.api.main import app

client = TestClient(app)


def test_root_health():
    root = client.get('/')
    health = client.get('/health')

    assert root.status_code == 200
    assert root.json() == {'Hello': 'World'}
    assert health.status_code == 200
    assert health.json() == {'status': 'ok'}


def test_pack(simple_test):
    response = client.post('/pack', json=simple_test)

    assert response.status_code == 200

    data = response.json()

    assert 'placed' in data
    assert 'unplaced' in data
    assert 'utilization' in data
    assert 'runtime_ms' in data
    assert 'notes' in data


def test_bad_pack():
    response = client.post('/pack', json={'truck': {'id': 't'}, 'boxes': []})

    assert response.status_code == 422
