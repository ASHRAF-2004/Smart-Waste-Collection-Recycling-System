"""Route optimization data structures and stubs for future API integration."""
from dataclasses import dataclass


@dataclass
class RouteStop:
    stop_id: str
    latitude: float
    longitude: float
    demand_kg: float


@dataclass
class Vehicle:
    vehicle_id: str
    capacity_kg: float


def compute_optimal_path(stops: list[RouteStop], vehicle: Vehicle) -> list[RouteStop]:
    """Stub for future integration with Google Maps API / OR-tools.

    Current behavior returns the input order.
    """
    if vehicle.capacity_kg <= 0:
        raise ValueError("Vehicle capacity must be positive.")
    return stops
