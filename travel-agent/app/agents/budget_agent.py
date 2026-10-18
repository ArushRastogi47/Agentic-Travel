"""
Budget Agent — DETERMINISTIC budget calculations.

No LLM is used here.  Pure Python arithmetic as specified in the spec.
"""

from __future__ import annotations

from app.graph.state import TravelState
from app.logging_config import logger
from app.models.schemas import BudgetAnalysis
from app.tools.routing import get_routing_provider


# ── Per-destination daily cost estimates (INR) ─────────────────────────
_DAILY_FOOD: dict[str, int] = {
    "dubai": 2500,
    "paris": 3500,
    "london": 3500,
    "new york": 4000,
    "tokyo": 3000,
    "singapore": 2000,
    "bangkok": 1200,
    "goa": 1000,
    "jaipur": 800,
    "bali": 1500,
    "maldives": 3000,
}

_DAILY_ACTIVITIES: dict[str, int] = {
    "dubai": 2000,
    "paris": 2500,
    "london": 2500,
    "new york": 3000,
    "tokyo": 2000,
    "singapore": 1500,
    "bangkok": 1000,
    "goa": 800,
    "jaipur": 600,
    "bali": 1200,
    "maldives": 2000,
}


def budget_agent(state: TravelState) -> dict:
    """
    LangGraph node — deterministic budget calculation.
    Uses cheapest flight + cheapest hotel + estimated daily costs.
    """
    constraints = state.get("trip_constraints", {})
    destination = constraints.get("destination", "").lower()
    duration = constraints.get("duration_days", 4)
    user_budget = constraints.get("budget", 0)
    nights = max(duration - 1, 1)

    logger.info(f"[Budget Agent] Calculating for {destination}, {duration} days")

    prev_status = state.get("workflow_status", [])

    # ── Flight cost (cheapest option) ──────────────────────────────
    flights = state.get("flight_results", [])
    flight_cost = 0.0
    if flights:
        cheapest = min(flights, key=lambda f: f.get("price", float("inf")))
        flight_cost = cheapest.get("price", 0)
        # Round trip
        flight_cost *= 2

    # ── Hotel cost (cheapest option) ───────────────────────────────
    hotels = state.get("hotel_results", [])
    hotel_cost = 0.0
    if hotels:
        cheapest_hotel = min(hotels, key=lambda h: h.get("nightly_price", float("inf")))
        hotel_cost = cheapest_hotel.get("nightly_price", 0) * nights

    # ── Transport ──────────────────────────────────────────────────
    routing = get_routing_provider()
    transport_info = routing.estimate_transport(destination, duration)
    transport_cost = transport_info.get("total_transport_cost", 0)

    # ── Food ───────────────────────────────────────────────────────
    daily_food = _DAILY_FOOD.get(destination, 1500)
    food_cost = daily_food * duration

    # ── Activities ─────────────────────────────────────────────────
    daily_act = _DAILY_ACTIVITIES.get(destination, 1500)
    activities_cost = daily_act * duration

    # ── Miscellaneous (10% buffer) ─────────────────────────────────
    subtotal = flight_cost + hotel_cost + transport_cost + food_cost + activities_cost
    misc = round(subtotal * 0.10, 2)

    total = round(subtotal + misc, 2)
    remaining = round(user_budget - total, 2) if user_budget > 0 else 0
    within = total <= user_budget if user_budget > 0 else True

    analysis = BudgetAnalysis(
        flights=flight_cost,
        hotels=hotel_cost,
        transport=transport_cost,
        food=food_cost,
        activities=activities_cost,
        miscellaneous=misc,
        estimated_total=total,
        user_budget=user_budget,
        remaining_budget=remaining,
        within_budget=within,
    )

    logger.info(
        f"[Budget Agent] Total: ₹{total:,.0f}  "
        f"Budget: ₹{user_budget:,.0f}  "
        f"Within: {within}"
    )

    return {
        "budget_analysis": analysis.model_dump(mode="json"),
        "workflow_status": ["✅ Budget calculated"],
    }


