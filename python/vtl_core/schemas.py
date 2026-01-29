from pydantic import BaseModel
from typing import List, Optional

class Box(BaseModel):
    id: str
    width: float
    height: float
    depth: float
    weight: float
    rotatable: bool = False
    priority: Optional[float] = 0.0

class Truck(BaseModel):
    id: str
    width: float
    height: float
    depth: float
    max_weight: Optional[float] = None

class PackingRequest(BaseModel):
    truck: Truck
    boxes: List[Box]

class PlacedBox(BaseModel):
    id: str
    x: float
    y: float
    z: float
    rotation: int  # e.g. 0–5 for orthogonal rotations

class PackingResponse(BaseModel):
    placed: List[PlacedBox]
    unplaced: List[str]
    utilization: float
    runtime_ms: float
    notes: List[str]
