from fastapi.testclient import TestClient
from python.api.main import app

import json
import pytest
from pathlib import Path

client = TestClient(app)


SAMPLE_FILES = [
    "0_axis.json",
    "1_simple.json",
    "2_many.json",
    "3_warehouse.json",
    "4_small_med.json",
    "5_furniture.json",
    "6_dense.json",
    "7_perfect_tile.json",
    "8_oversized.json",
    "9_tall_skinny.json",
    "10_many_small.json",
    "11_fragmentation.json",
    "12_flat.json",
    "13_single_type.json",
]


@pytest.mark.parametrize("sample_file", SAMPLE_FILES)
def test_all_sample_payloads(client, sample_file):
    sample_path = Path(__file__).parent / sample_file

    with sample_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    response = client.post("/pack", json=payload)

    assert response.status_code == 200, response.text

    data = response.json()

    assert "placed" in data
    assert "unplaced" in data
    assert "utilization" in data
    assert "runtime_ms" in data
    assert "notes" in data

    assert len(data["placed"]) + len(data["unplaced"]) == len(payload["boxes"])
    assert data["utilization"] >= 0
    assert data["runtime_ms"] > 0