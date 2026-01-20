# API Reference

## How to Run
cd VTL
uvicorn python.api.main:app

## Base URL
http://127.0.0.1:8000/

## Endpoints

---

### `GET /health`
Checks backend status.

#### Response
```json
{ "status": "ok" }
```

### `POST /pack`
Runs packing algorithm.

#### Request Body
```json
{
  "truck": {
    "id": "T1",
    "width": 2.4,
    "height": 2.6,
    "depth": 12.0
  },
  "boxes": [
    {
      "id": "bx1",
      "width": 1.2,
      "height": 0.8,
      "depth": 0.6,
      "weight": 12.0,
      "rotatable": true,
      "priority": 0.0
    }
  ]
}
```

#### Response Body
```json
{
  "placed": [
    {
      "id": "bx1",
      "x": 0.0,
      "y": 0.0,
      "z": 0.0,
      "rotation": 1
    }
  ],
  "unplaced": [
    {
      "id": "bx2"
    }
  ],
  "utilization": 0.27,
  "runtime_ms": 7500,
  "notes": "first_fit_layered"
}
```

#### Error Responses
```js
400 Bad Request
422 Validation Error
500 Internal Server Error
```

## Data Models Overview
- Box
- Truck
- PackingRequest
- PlacedBox
- PackingResponse
