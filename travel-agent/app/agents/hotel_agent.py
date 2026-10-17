"""
Hotel Agent — searches for accommodation using the configured provider.
Mostly a data-fetching node (not LLM-heavy).
"""

from __future__ import annotations

from app.graph.state import TravelState
from app.logging_config import logger
from app.tools.hotels import get_hotel_provider


def hotel_agent(state: TravelState) -> dict:
    """LangGraph node — fetch hotel options."""
    constraints = state.get("trip_constraints", {})
    destination = constraints.get("destination", "")
    start_date = constraints.get("start_date", "")
    end_date = constraints.get("end_date", "")
    nights = constraints.get("duration_days", 4) - 1  # check-in day doesn't count

    if nights < 1:
        nights = constraints.get("duration_days", 4)

    logger.info(f"[Hotel Agent] Searching: {destination} ({nights} nights)")

    prev_status = state.get("workflow_status", [])

    try:
        provider = get_hotel_provider()
        results = provider.search_hotels(destination, start_date, end_date, nights)
        hotels = [r.model_dump() for r in results]
        logger.info(f"[Hotel Agent] Found {len(hotels)} options")
        return {
            "hotel_results": hotels,
            "workflow_status": prev_status + ["✅ Hotel research complete"],
        }
    except Exception as exc:
        logger.error(f"[Hotel Agent] Failed: {exc}")
        return {
            "hotel_results": [],
            "workflow_status": prev_status + ["⚠️ Hotel research failed (continuing without)"],
        }
