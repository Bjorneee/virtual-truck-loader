from fastapi.testclient import TestClient
from python.api.main import app

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TEST_DATA = Path(__file__).resolve().parent


def load_payload(name: str) -> dict:
    with open(TEST_DATA / name, 'r', encoding='utf-8') as f:
        return json.load(f)
    

@pytest.fixture
def client():
    return TestClient(app)

# @pytest.fixture
# def axis_test() -> dict:
#     return load_payload('0_axis.json')

@pytest.fixture
def simple_test() -> dict:
    return load_payload('1_simple.json')

# @pytest.fixture
# def many_test() -> dict:
#     return load_payload('2_many.json')

# @pytest.fixture
# def warehouse_test() -> dict:
#     return load_payload('3_warehouse.json')

# @pytest.fixture
# def small_med_test() -> dict:
#     return load_payload('4_small_med.json')

# @pytest.fixture
# def furniture_test() -> dict:
#     return load_payload('5_furniture.json')

# @pytest.fixture
# def dense_test() -> dict:
#     return load_payload('6_dense.json')

# @pytest.fixture
# def perfect_tile_test() -> dict:
#     return load_payload('7_perfect_tile.json')

# @pytest.fixture
# def oversized_test() -> dict:
#     return load_payload('8_oversized.json')

# @pytest.fixture
# def tall_skinny_test() -> dict:
#     return load_payload('9_tall_skinny.json')

# @pytest.fixture
# def many_small_test() -> dict:
#     return load_payload('10_many_small.json')

# @pytest.fixture
# def fragmentation_test() -> dict:
#     return load_payload('11_fragmentation.json')

# @pytest.fixture
# def flat_test() -> dict:
#     return load_payload('12_flat.json')

# @pytest.fixture
# def single_type_test() -> dict:
#     return load_payload('13_single_type.json')