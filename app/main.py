"""Vehicle Service API.

A Python (FastAPI) implementation of the Vehicle Service Collection:
- POST   /vehicles       Create a vehicle
- GET    /vehicles/{id}  Retrieve a vehicle
- PATCH  /vehicles/{id}  Update a vehicle
- DELETE /vehicles/{id}  Delete a vehicle

Behavior (status codes, validation and error messages) mirrors the
examples saved in the Postman collection.
"""
from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError

app = FastAPI(
    title="Vehicle Service API",
    version="1.0.0",
    description="Implements the Vehicle Service Collection.",
)

# ---------------------------------------------------------------------------
# In-memory data store
# ---------------------------------------------------------------------------
_vehicles: dict[int, dict] = {}
_next_id: int = 1


def _seed() -> None:
    """Seed the store so GET /vehicles/1 works out of the box."""
    global _next_id
    _vehicles[1] = {
        "id": 1,
        "nickName": "The Lisa Marie",
        "vin": "4M2DV11W4RDJ53329",
        "make": "Mercury",
        "model": "Villager",
        "year": "1994",
        "miles": 159864,
    }
    _next_id = 2


_seed()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class VehicleCreate(BaseModel):
    nickName: str = Field(..., min_length=1)
    vin: str = Field(..., min_length=1)
    make: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1)
    year: str = Field(..., min_length=1)
    miles: int

    model_config = {"extra": "forbid"}


class VehicleUpdate(BaseModel):
    nickName: Optional[str] = None
    vin: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[str] = None
    miles: Optional[int] = None

    model_config = {"extra": "forbid"}


# Required attributes, in the order the collection reports them.
_REQUIRED = ["nickName", "vin", "make", "model", "year", "miles"]


def _error(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"message": message})


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.post("/vehicles")
async def create_vehicle(payload: dict):
    """Create a vehicle.

    Returns 400 for a missing required attribute, 409 if the VIN already
    exists, otherwise 201 with the created vehicle.
    """
    global _next_id

    for key in _REQUIRED:
        value = payload.get(key)
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return _error(
                status.HTTP_400_BAD_REQUEST,
                f"Request body missing required attribute: {key}",
            )

    vin = payload["vin"]
    for existing in _vehicles.values():
        if existing["vin"] == vin:
            return _error(
                status.HTTP_409_CONFLICT,
                f"Vehicle with VIN {vin} already exists. "
                f"Existing vehicle ID: {existing['id']}",
            )

    vehicle = {
        "id": _next_id,
        "nickName": payload["nickName"],
        "vin": payload["vin"],
        "make": payload["make"],
        "model": payload["model"],
        "year": payload["year"],
        "miles": payload["miles"],
    }
    _vehicles[_next_id] = vehicle
    _next_id += 1
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=vehicle)


@app.get("/vehicles/{vehicle_id}")
async def retrieve_vehicle(vehicle_id: int):
    """Retrieve a vehicle by id, or 404 if it does not exist."""
    vehicle = _vehicles.get(vehicle_id)
    if vehicle is None:
        return _error(
            status.HTTP_404_NOT_FOUND,
            f"Vehicle with id: {vehicle_id} not found.",
        )
    return vehicle


@app.patch("/vehicles/{vehicle_id}")
async def update_vehicle(vehicle_id: int, payload: dict):
    """Partially update a vehicle.

    Returns 404 if not found, 400 for a bad/empty body, 409 if the new VIN
    collides with a different vehicle, otherwise 200 with the updated record.
    """
    vehicle = _vehicles.get(vehicle_id)
    if vehicle is None:
        return _error(
            status.HTTP_404_NOT_FOUND,
            f"Vehicle with id: {vehicle_id} not found.",
        )

    if not isinstance(payload, dict) or len(payload) == 0:
        return _error(status.HTTP_400_BAD_REQUEST, "Bad request body.")

    allowed = set(_REQUIRED)
    unknown = [k for k in payload if k not in allowed]
    if unknown:
        return _error(status.HTTP_400_BAD_REQUEST, "Bad request body.")

    new_vin = payload.get("vin")
    if new_vin is not None:
        for other in _vehicles.values():
            if other["vin"] == new_vin and other["id"] != vehicle_id:
                return _error(
                    status.HTTP_409_CONFLICT,
                    f"Vehicle with VIN {new_vin} already exists. "
                    f"Existing vehicle ID: {other['id']}",
                )

    vehicle.update({k: v for k, v in payload.items() if v is not None})
    vehicle["id"] = vehicle_id
    return vehicle


@app.delete("/vehicles/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle(vehicle_id: int):
    """Delete a vehicle. Returns 204 on success, 404 if not found."""
    if vehicle_id not in _vehicles:
        return _error(
            status.HTTP_404_NOT_FOUND,
            f"Vehicle with id: {vehicle_id} not found.",
        )
    del _vehicles[vehicle_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)
