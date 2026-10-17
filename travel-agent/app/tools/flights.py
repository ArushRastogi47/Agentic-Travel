"""
Flight provider — adapter pattern.
  FlightProvider (Protocol)
    ├── OpenSkyAdapter       (free, limited live data)
    └── MockFlightAdapter    (offline demo)
"""

from __future__ import annotations

import random
from typing import Protocol

from app.config import DEMO_MODE
from app.logging_config import logger
from app.models.schemas import DataType, FlightResult


class FlightProvider(Protocol):
    def search_flights(
        self, origin: str, destination: str, date: str, travelers: int
    ) -> list[FlightResult]: ...


# ── Mock (demo) ────────────────────────────────────────────────────────

class MockFlightAdapter:
    """Returns realistic estimated flight data for demonstration."""

    _AIRLINES = [
        "Air India", "IndiGo", "SpiceJet", "Vistara",
        "Emirates", "Etihad", "Qatar Airways", "Fly Dubai",
    ]
    _PRICE_RANGES: dict[str, tuple[int, int]] = {
        "dubai": (12000, 25000),
        "paris": (30000, 55000),
        "london": (28000, 50000),
        "new york": (40000, 75000),
        "tokyo": (25000, 50000),
        "singapore": (15000, 30000),
        "bangkok": (10000, 22000),
        "bali": (18000, 35000),
        "goa": (3000, 8000),
        "jaipur": (3000, 7000),
        "maldives": (18000, 40000),
    }

    def search_flights(
        self, origin: str, destination: str, date: str, travelers: int
    ) -> list[FlightResult]:
        logger.info(f"[Flights] MOCK: {origin} → {destination} on {date}")
        dest_lower = destination.lower()
        lo, hi = self._PRICE_RANGES.get(dest_lower, (15000, 35000))

        results = []
        for _ in range(random.randint(3, 5)):
            airline = random.choice(self._AIRLINES)
            price = round(random.uniform(lo, hi), -2)  # round to 100s
            duration = random.randint(120, 480)
            dep_h = random.randint(5, 22)
            results.append(
                FlightResult(
                    airline=airline,
                    origin=origin or "DEL",
                    destination=destination.upper()[:3] if len(destination) >= 3 else destination.upper(),
                    departure=f"{date}T{dep_h:02d}:00",
                    arrival=f"{date}T{(dep_h + duration // 60) % 24:02d}:{duration % 60:02d}",
                    duration_minutes=duration,
                    price=price * travelers,
                    currency="INR",
                    source="Mock",
                    data_type=DataType.MOCK,
                )
            )
        # sort cheapest first
        results.sort(key=lambda f: f.price)
        return results


# ── Factory ────────────────────────────────────────────────────────────

def get_flight_provider() -> FlightProvider:
    return MockFlightAdapter()
