"""
Weather Agent — fetches weather information for the destination.
Mostly deterministic after obtaining API data.
"""

from __future__ import annotations

from app.graph.state import TravelState
from app.logging_config import logger
from app.tools.weather import get_weather_provider


def weather_agent(state: TravelState) -> dict:
    """LangGraph node — fetch weather data."""
    selected = state.get("selected_agents", ["weather"])
    if "weather" not in selected:
        logger.info("[Weather Agent] Skipping (not in selected_agents)")
        return {}

    constraints = state.get("trip_constraints", {})
    destination = constraints.get("destination", "")
    start_date = constraints.get("start_date", "")
    end_date = constraints.get("end_date", "")

    logger.info(f"[Weather Agent] Fetching weather for {destination}")

    try:
        provider = get_weather_provider()
        info = provider.get_weather(destination, start_date, end_date)
        logger.info(
            f"[Weather Agent] Got {len(info.daily)} days of weather data"
        )
        return {
            "weather_info": info.model_dump(mode="json"),
            "workflow_status": ["✅ Weather research complete"],
        }

    except Exception as exc:
        logger.error(f"[Weather Agent] Failed: {exc}")
        return {
            "weather_info": {},
            "workflow_status": ["⚠️ Weather data unavailable (continuing without)"],
        }

