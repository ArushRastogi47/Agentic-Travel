"""
Weather provider — adapter pattern.
  WeatherProvider (Protocol)
    ├── OpenMeteoWeatherProvider  (free live API)
    └── MockWeatherProvider       (offline demo)
"""

from __future__ import annotations

import random
from typing import Protocol

import httpx

from app.config import DEMO_MODE, OPEN_METEO_BASE_URL
from app.logging_config import logger
from app.models.schemas import DailyWeather, DataType, WeatherInfo


# ── Protocol ───────────────────────────────────────────────────────────

class WeatherProvider(Protocol):
    def get_weather(
        self, location: str, start_date: str, end_date: str
    ) -> WeatherInfo: ...


# ── Open-Meteo (free, no key) ─────────────────────────────────────────

class OpenMeteoWeatherProvider:
    """Uses the Open-Meteo free API — no API key required."""

    # Simple geocoding lookup for common destinations
    _GEOCODE: dict[str, tuple[float, float]] = {
        "dubai": (25.276987, 55.296249),
        "paris": (48.856614, 2.352222),
        "london": (51.507351, -0.127758),
        "new york": (40.712776, -74.005974),
        "tokyo": (35.689487, 139.691711),
        "singapore": (1.352083, 103.819836),
        "bangkok": (13.756331, 100.501762),
        "rome": (41.902784, 12.496366),
        "bali": (-8.340539, 115.091949),
        "mumbai": (19.075983, 72.877656),
        "delhi": (28.613939, 77.209023),
        "goa": (15.299326, 74.123993),
        "jaipur": (26.912434, 75.787271),
        "istanbul": (41.008238, 28.978359),
        "maldives": (3.202778, 73.220833),
    }

    def get_weather(
        self, location: str, start_date: str, end_date: str
    ) -> WeatherInfo:
        coords = self._GEOCODE.get(location.lower())
        if not coords:
            logger.warning(
                f"[Weather] No geocode for '{location}', falling back to mock"
            )
            return MockWeatherProvider().get_weather(location, start_date, end_date)

        lat, lon = coords
        url = (
            f"{OPEN_METEO_BASE_URL}/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max"
            f"&start_date={start_date}&end_date={end_date}"
            f"&timezone=auto"
        )
        try:
            resp = httpx.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            daily_data = data.get("daily", {})
            dates = daily_data.get("time", [])
            highs = daily_data.get("temperature_2m_max", [])
            lows = daily_data.get("temperature_2m_min", [])
            rain = daily_data.get("precipitation_probability_max", [])

            daily = []
            for i, d in enumerate(dates):
                h = highs[i] if i < len(highs) else 30.0
                l_ = lows[i] if i < len(lows) else 20.0
                r = rain[i] if i < len(rain) else 0
                desc = "Sunny" if r < 30 else ("Partly cloudy" if r < 60 else "Rainy")
                daily.append(
                    DailyWeather(
                        date=d,
                        temperature_high=h,
                        temperature_low=l_,
                        rain_probability=r,
                        description=desc,
                    )
                )

            packing = self._packing_suggestions(daily)
            return WeatherInfo(
                location=location,
                daily=daily,
                packing_suggestions=packing,
                source="Open-Meteo",
                data_type=DataType.LIVE,
            )
        except Exception as exc:
            logger.error(f"[Weather] Open-Meteo failed: {exc}")
            return MockWeatherProvider().get_weather(location, start_date, end_date)

    @staticmethod
    def _packing_suggestions(daily: list[DailyWeather]) -> list[str]:
        suggestions = []
        avg_high = sum(d.temperature_high for d in daily) / max(len(daily), 1)
        any_rain = any(d.rain_probability > 40 for d in daily)
        if avg_high > 30:
            suggestions.append("Light, breathable clothing")
            suggestions.append("Sunscreen and sunglasses")
            suggestions.append("Hat or cap")
        elif avg_high > 20:
            suggestions.append("Comfortable layers")
        else:
            suggestions.append("Warm jacket")
            suggestions.append("Layered clothing")
        if any_rain:
            suggestions.append("Umbrella or rain jacket")
        suggestions.append("Comfortable walking shoes")
        return suggestions


# ── Mock (offline demo) ───────────────────────────────────────────────

class MockWeatherProvider:
    """Returns realistic-looking demo weather data."""

    def get_weather(
        self, location: str, start_date: str, end_date: str
    ) -> WeatherInfo:
        logger.info(f"[Weather] Using MOCK data for {location}")
        from datetime import datetime, timedelta

        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            num_days = (end - start).days + 1
        except (ValueError, TypeError):
            start = datetime.now()
            num_days = 4

        daily = []
        for i in range(num_days):
            d = start + timedelta(days=i)
            high = round(random.uniform(28, 38), 1)
            low = round(high - random.uniform(5, 10), 1)
            rain = round(random.uniform(0, 30), 0)
            daily.append(
                DailyWeather(
                    date=d.strftime("%Y-%m-%d"),
                    temperature_high=high,
                    temperature_low=low,
                    rain_probability=rain,
                    description="Sunny" if rain < 20 else "Partly cloudy",
                )
            )

        return WeatherInfo(
            location=location,
            daily=daily,
            packing_suggestions=[
                "Light, breathable clothing",
                "Sunscreen and sunglasses",
                "Comfortable walking shoes",
                "Hat or cap",
            ],
            source="Mock",
            data_type=DataType.MOCK,
        )


# ── Factory ────────────────────────────────────────────────────────────

def get_weather_provider() -> WeatherProvider:
    if DEMO_MODE:
        return MockWeatherProvider()
    return OpenMeteoWeatherProvider()
