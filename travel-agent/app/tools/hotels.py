"""
Hotel provider — adapter pattern.
  HotelProvider (Protocol)
    ├── OpenStreetMapAdapter  (free, limited)
    └── MockHotelAdapter      (offline demo)
"""

from __future__ import annotations

import random
from typing import Protocol

from app.config import DEMO_MODE
from app.logging_config import logger
from app.models.schemas import DataType, HotelResult


class HotelProvider(Protocol):
    def search_hotels(
        self, destination: str, check_in: str, check_out: str, nights: int
    ) -> list[HotelResult]: ...


# ── Mock (demo) ────────────────────────────────────────────────────────

class MockHotelAdapter:
    """Returns realistic estimated hotel data for demonstration."""

    _HOTELS: dict[str, list[dict]] = {
        "dubai": [
            {"name": "Rove Downtown Dubai", "rating": 4.2, "nightly": 5500,
             "amenities": ["WiFi", "Pool", "Gym", "Restaurant"]},
            {"name": "Ibis Styles Dubai Airport", "rating": 3.8, "nightly": 3800,
             "amenities": ["WiFi", "Restaurant", "Airport Shuttle"]},
            {"name": "Gevora Hotel", "rating": 4.5, "nightly": 8000,
             "amenities": ["WiFi", "Pool", "Spa", "Gym", "Restaurant", "Bar"]},
            {"name": "Premier Inn Dubai Al Jaddaf", "rating": 4.0, "nightly": 4200,
             "amenities": ["WiFi", "Restaurant", "Gym"]},
            {"name": "Atlantis The Palm", "rating": 4.8, "nightly": 18000,
             "amenities": ["WiFi", "Pool", "Spa", "Waterpark", "Beach", "Restaurant"]},
        ],
        "default": [
            {"name": "City Center Hotel", "rating": 4.0, "nightly": 4500,
             "amenities": ["WiFi", "Restaurant"]},
            {"name": "Budget Inn", "rating": 3.5, "nightly": 2500,
             "amenities": ["WiFi"]},
            {"name": "Grand Plaza Hotel", "rating": 4.3, "nightly": 7000,
             "amenities": ["WiFi", "Pool", "Gym", "Restaurant"]},
            {"name": "Comfort Suites", "rating": 3.8, "nightly": 3500,
             "amenities": ["WiFi", "Breakfast"]},
        ],
    }

    def search_hotels(
        self, destination: str, check_in: str, check_out: str, nights: int
    ) -> list[HotelResult]:
        logger.info(f"[Hotels] MOCK: {destination} ({nights} nights)")
        hotels_data = self._HOTELS.get(destination.lower(), self._HOTELS["default"])

        results = []
        for h in hotels_data:
            nightly = h["nightly"] + random.randint(-500, 500)
            results.append(
                HotelResult(
                    name=h["name"],
                    location=destination,
                    nightly_price=nightly,
                    total_price=nightly * nights,
                    rating=h["rating"],
                    amenities=h["amenities"],
                    source="Mock",
                    data_type=DataType.MOCK,
                )
            )
        results.sort(key=lambda h: h.nightly_price)
        return results


# ── Live OpenStreetMap Adapter (free, no key) ──────────────────────────

class OpenStreetMapHotelAdapter:
    """Queries OpenStreetMap Overpass API for real accommodations, with mock fallback."""

    def search_hotels(
        self, destination: str, check_in: str, check_out: str, nights: int
    ) -> list[HotelResult]:
        logger.info(f"[Hotels] OpenStreetMap lookup for {destination}")
        mock_fallback = MockHotelAdapter().search_hotels(destination, check_in, check_out, nights)
        try:
            import httpx

            query = f"""
            [out:json][timeout:5];
            area["name"="{destination}"]->.searchArea;
            (
              node["tourism"="hotel"]["name"](area.searchArea);
            );
            out 5;
            """
            resp = httpx.post(
                "https://overpass-api.de/api/interpreter",
                data={"data": query},
                headers={"User-Agent": "TravelPlannerAgent/1.0"},
                timeout=5.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                elements = data.get("elements", [])
                if elements:
                    results = []
                    for el in elements[:5]:
                        name = el.get("tags", {}).get("name", "Local Hotel")
                        results.append(
                            HotelResult(
                                name=name,
                                location=destination,
                                nightly_price=random.randint(3000, 7000),
                                total_price=random.randint(3000, 7000) * nights,
                                rating=round(random.uniform(3.8, 4.6), 1),
                                amenities=["WiFi", "Front Desk"],
                                source="OpenStreetMap",
                                data_type=DataType.LIVE,
                            )
                        )
                    return results
        except Exception as exc:
            logger.warning(f"[Hotels] OSM live query failed ({exc}), using mock fallback")

        return mock_fallback


# ── Factory ────────────────────────────────────────────────────────────

def get_hotel_provider() -> HotelProvider:
    if DEMO_MODE:
        return MockHotelAdapter()
    return OpenStreetMapHotelAdapter()

