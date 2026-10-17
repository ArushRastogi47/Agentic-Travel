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
    constraints = state.get("trip_constraints", {})
    destination = constraints.get("destination", "")
    origin = constraints.get("origin", "") or "Delhi"
    start_date = constraints.get("start_date", "")
    travelers = constraints.get("traveler_count", 1)

    logger.info(f"[Flight Agent] Searching: {origin} → {destination}")

    prev_status = state.get("workflow_status", [])

    try:
        provider = get_flight_provider()
        results = provider.search_flights(origin, destination, start_date, travelers)
        flights = [r.model_dump() for r in results]
        logger.info(f"[Flight Agent] Found {len(flights)} options")
        return {
            "flight_results": flights,
            "workflow_status": prev_status + ["✅ Flight research complete"],
        }
    except Exception as exc:
        logger.error(f"[Flight Agent] Failed: {exc}")
        return {
            "flight_results": [],
            "workflow_status": prev_status + ["⚠️ Flight research failed (continuing without)"],
        }
