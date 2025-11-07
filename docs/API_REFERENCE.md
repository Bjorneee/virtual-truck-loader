# API Reference

## Base URL
http://127.0.0.1:5000

## Endpoints

---

### `GET /health`
Checks backend status.

#### Response
```json
{ "ok": true }
```

### `POST /load`
Runs packing algorithm.

#### Request Body
```json
{
  "truck": {
    "id": "T1",
    "inner_w": 2.4,
    "inner_h": 2.6,
    "inner_d": 12.0
  },
  "boxes": [
    {
      "id": "bx1",
      "w": 1.2,
      "h": 0.8,
      "d": 0.6,
      "weight": 12.0,
      "rotatable": true,
      "priority": 0
    }
  ]
}
```

#### Response Body
```json
{
  "placements": [
    {
      "id": "bx1",
      "x": 0.0,
      "y": 0.0,
      "z": 0.0,
      "rw": 1.2,
      "rh": 0.8,
      "rd": 0.6,
      "rotation": "whd"
    }
  ],
  "utilization": 0.27,
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
- TruckIn
- BoxIn
- LoadRequest
- Placement
- LoadResponse
