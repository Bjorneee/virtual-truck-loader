from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class Box(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    width: float
    height: float
    depth: float
    weight: float
    rotatable: bool = True
    priority: Optional[float] = 0.0

class Truck(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    width: float
    height: float
    depth: float
    max_weight: Optional[float] = None

class PackingRequest(BaseModel):
    truck: Truck
    boxes: List[Box]

class PlacedBox(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    x: float
    y: float
    z: float
    rotation: int  # e.g. 0–5 for orthogonal rotations

class UnplacedBox(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str # e.g. "too large", "exceeds weight limit", etc.

class PackingResponse(BaseModel):
    placed: Optional[List[PlacedBox]]
    unplaced: Optional[List[Box]]
    utilization: float
    runtime_ms: float
    notes: List[str]
