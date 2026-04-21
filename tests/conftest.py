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
def many_payload() -> dict:
    return load_payload('2_many.json')


@pytest.fixture
def warehouse_payload() -> dict:
    return load_payload('3_warehouse.json')


@pytest.fixture
def fragmentation_payload() -> dict:
    return load_payload('11_fragmentation.json')
