"""
Places provider — adapter pattern.
Returns popular attractions / points of interest for a destination.
"""

from __future__ import annotations

from typing import Protocol

from app.logging_config import logger
from app.models.schemas import DataType


class PlacesProvider(Protocol):
    def get_places(self, destination: str) -> list[dict]: ...


class MockPlacesProvider:
    """Returns curated attraction lists for popular destinations."""

    _PLACES: dict[str, list[dict]] = {
        "dubai": [
            {"name": "Burj Khalifa", "category": "Landmark", "est_cost": 1500, "duration_hours": 2},
            {"name": "Dubai Mall", "category": "Shopping", "est_cost": 0, "duration_hours": 3},
            {"name": "Dubai Marina", "category": "Sightseeing", "est_cost": 0, "duration_hours": 2},
            {"name": "Palm Jumeirah", "category": "Beach", "est_cost": 0, "duration_hours": 3},
            {"name": "Dubai Museum", "category": "Culture", "est_cost": 300, "duration_hours": 1.5},
            {"name": "Gold Souk", "category": "Shopping", "est_cost": 0, "duration_hours": 1.5},
            {"name": "Desert Safari", "category": "Adventure", "est_cost": 3000, "duration_hours": 5},
            {"name": "Global Village", "category": "Entertainment", "est_cost": 500, "duration_hours": 4},
            {"name": "Jumeirah Beach", "category": "Beach", "est_cost": 0, "duration_hours": 3},
            {"name": "Dubai Frame", "category": "Landmark", "est_cost": 500, "duration_hours": 1},
        ],
        "paris": [
            {"name": "Eiffel Tower", "category": "Landmark", "est_cost": 2000, "duration_hours": 2},
            {"name": "Louvre Museum", "category": "Culture", "est_cost": 1500, "duration_hours": 3},
            {"name": "Notre-Dame", "category": "Landmark", "est_cost": 0, "duration_hours": 1},
            {"name": "Champs-Élysées", "category": "Shopping", "est_cost": 0, "duration_hours": 2},
            {"name": "Montmartre", "category": "Sightseeing", "est_cost": 0, "duration_hours": 2},
        ],
        "default": [
            {"name": "City Center Walk", "category": "Sightseeing", "est_cost": 0, "duration_hours": 2},
            {"name": "Local Museum", "category": "Culture", "est_cost": 500, "duration_hours": 2},
            {"name": "Famous Market", "category": "Shopping", "est_cost": 0, "duration_hours": 2},
            {"name": "Popular Park", "category": "Nature", "est_cost": 0, "duration_hours": 2},
        ],
    }

    def get_places(self, destination: str) -> list[dict]:
        logger.info(f"[Places] MOCK: attractions for {destination}")
        places = self._PLACES.get(destination.lower(), self._PLACES["default"])
        for p in places:
            p["source"] = "Mock"
            p["data_type"] = DataType.MOCK.value
        return places


def get_places_provider() -> PlacesProvider:
    return MockPlacesProvider()
