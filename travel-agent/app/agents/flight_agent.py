"""
Flight Agent — searches for flights using the configured provider.
Mostly a data-fetching node (not LLM-heavy).
"""

from __future__ import annotations

from app.graph.state import TravelState
from app.logging_config import logger
from app.tools.flights import get_flight_provider


def flight_agent(state: TravelState) -> dict:
    """LangGraph node — fetch flight options."""
    selected = state.get("selected_agents", ["flight"])
    if "flight" not in selected:
        logger.info("[Flight Agent] Skipping (not in selected_agents)")
        return {}

    constraints = state.get("trip_constraints", {})
    destination = constraints.get("destination", "")
    origin = constraints.get("origin", "") or "Delhi"
    start_date = constraints.get("start_date", "")
    travelers = constraints.get("traveler_count", 1)

    logger.info(f"[Flight Agent] Searching: {origin} → {destination}")

    try:
        provider = get_flight_provider()
        results = provider.search_flights(origin, destination, start_date, travelers)
        flights = [r.model_dump(mode="json") for r in results]

        logger.info(f"[Flight Agent] Found {len(flights)} options")
        return {
            "flight_results": flights,
            "workflow_status": ["✅ Flight research complete"],
        }
    except Exception as exc:
        logger.error(f"[Flight Agent] Failed: {exc}")
        return {
            "flight_results": [],
            "workflow_status": ["⚠️ Flight research failed (continuing without)"],
        }

