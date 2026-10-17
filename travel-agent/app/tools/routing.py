"""
Routing / transport estimation provider.
Estimates local transport costs and durations.
"""

from __future__ import annotations

from typing import Protocol

from app.logging_config import logger


class RoutingProvider(Protocol):
    def estimate_transport(
        self, destination: str, duration_days: int
    ) -> dict: ...


class MockRoutingProvider:
    """Estimates daily local transport costs per destination."""

    _DAILY_TRANSPORT: dict[str, int] = {
        "dubai": 800,
        "paris": 1200,
        "london": 1500,
        "new york": 1800,
        "tokyo": 1000,
        "singapore": 600,
        "bangkok": 400,
        "goa": 500,
        "jaipur": 400,
        "bali": 600,
        "maldives": 500,
    }

    def estimate_transport(
        self, destination: str, duration_days: int
    ) -> dict:
        logger.info(f"[Routing] MOCK: transport estimate for {destination}")
        daily = self._DAILY_TRANSPORT.get(destination.lower(), 700)
        return {
            "daily_transport_cost": daily,
            "total_transport_cost": daily * duration_days,
            "currency": "INR",
            "mode": "Taxi / Metro / Rideshare",
            "source": "Mock",
            "data_type": "estimated",
        }


def get_routing_provider() -> RoutingProvider:
    return MockRoutingProvider()
