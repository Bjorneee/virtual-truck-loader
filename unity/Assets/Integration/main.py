from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}\



class Box(BaseModel):
    id: str
    width: float
    height: float
    depth: float
    weight: float
    rotatable: bool
    priority: float

class Truck(BaseModel):
    id: str
    width: float
    height: float
    depth: float

class PackingRequest(BaseModel):
    truck: Truck
    boxes: List[Box]

class PlacedBox(BaseModel):
    id: str
    x: float
    y: float
    z: float
    rotation: int

class PackingResponse(BaseModel):
    placed: List[PlacedBox]
    unplaced: list
    utilization: float
    runtime_ms: int
    notes: str

@app.post("/pack")
def pack(request: PackingRequest):
    # TEMP: fake response so Unity can test
    placed = []
    for i, box in enumerate(request.boxes):
        placed.append({
            "id": box.id,
            "x": i * 1.5,
            "y": 0.0,
            "z": 0.0,
            "rotation": 0
        })

    return {
        "placed": placed,
        "unplaced": [],
        "utilization": 0.5,
        "runtime_ms": 10,
        "notes": "test layout"
    }