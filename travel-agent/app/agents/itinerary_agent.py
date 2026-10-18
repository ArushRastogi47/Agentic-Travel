"""
Itinerary Agent — uses the LLM to convert research results into
a day-by-day travel plan.
"""

from __future__ import annotations

import json
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from app.graph.state import TravelState
from app.logging_config import logger
from app.tools.llm import get_llm
from app.tools.places import get_places_provider


_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "itinerary.txt"


def itinerary_agent(state: TravelState) -> dict:
    """LangGraph node — generate a day-by-day itinerary using the LLM."""
    constraints = state.get("trip_constraints", {})
    destination = constraints.get("destination", "Unknown")
    duration = constraints.get("duration_days", 4)
    start_date = constraints.get("start_date", "")
    budget = constraints.get("budget", 0)
    currency = constraints.get("currency", "INR")

    logger.info(f"[Itinerary Agent] Generating {duration}-day plan for {destination}")

    prev_status = state.get("workflow_status", [])

    # ── Gather context ─────────────────────────────────────────────
    weather = state.get("weather_info", {})
    flights = state.get("flight_results", [])
    hotels = state.get("hotel_results", [])
    budget_data = state.get("budget_analysis", {})
    feedback = state.get("human_feedback", "")

    # Get attractions
    places_provider = get_places_provider()
    places = places_provider.get_places(destination)

    # Summarise data for the prompt
    weather_summary = _summarise_weather(weather)
    flight_summary = _summarise_flights(flights)
    hotel_summary = _summarise_hotels(hotels)
    budget_summary = _summarise_budget(budget_data)
    places_summary = _summarise_places(places)

    try:
        prompt_template = _PROMPT_PATH.read_text()
        prompt = prompt_template.format(
            destination=destination,
            duration_days=duration,
            start_date=start_date,
            budget=budget,
            currency=currency,
            weather_summary=weather_summary,
            flight_summary=flight_summary,
            hotel_summary=hotel_summary,
            budget_summary=budget_summary,
        )

        if places_summary:
            prompt += f"\n\nAvailable Attractions:\n{places_summary}"

        if feedback:
            prompt += f"\n\nUser Feedback (incorporate these changes):\n{feedback}"

        llm = get_llm(temperature=0.5)
        response = llm.invoke([
            SystemMessage(content="You are an expert travel planner."),
            HumanMessage(content=prompt),
        ])

        itinerary = response.content
        if isinstance(itinerary, list):
            itinerary = "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in itinerary)
        elif not isinstance(itinerary, str):
            itinerary = str(itinerary)

        logger.info("[Itinerary Agent] Plan generated successfully")

        return {
            "itinerary_plan": itinerary,
            "human_decision": "pending",
            "workflow_status": ["✅ Itinerary generated"],
        }

    except Exception as exc:
        logger.error(f"[Itinerary Agent] Failed: {exc}")
        # Generate a basic fallback itinerary
        fallback = _fallback_itinerary(destination, duration, places)
        return {
            "itinerary_plan": fallback,
            "human_decision": "pending",
            "workflow_status": ["⚠️ Itinerary generated (basic fallback)"],
        }



# ── Summarisers ───────────────────────────────────────────────────────

def _summarise_weather(weather: dict) -> str:
    if not weather:
        return "Weather data unavailable."
    daily = weather.get("daily", [])
    if not daily:
        return "Weather data unavailable."
    lines = []
    for d in daily[:7]:
        lines.append(
            f"  {d.get('date', '?')}: {d.get('description', '?')} "
            f"({d.get('temperature_low', '?')}–{d.get('temperature_high', '?')}°C, "
            f"rain {d.get('rain_probability', '?')}%)"
        )
    return "\n".join(lines)


def _summarise_flights(flights: list[dict]) -> str:
    if not flights:
        return "No flight data available."
    top = flights[:3]
    lines = []
    for f in top:
        lines.append(
            f"  {f.get('airline', '?')}: ₹{f.get('price', 0):,.0f} "
            f"({f.get('duration_minutes', 0)} min) [{f.get('data_type', '?')}]"
        )
    return "\n".join(lines)


def _summarise_hotels(hotels: list[dict]) -> str:
    if not hotels:
        return "No hotel data available."
    top = hotels[:3]
    lines = []
    for h in top:
        lines.append(
            f"  {h.get('name', '?')}: ₹{h.get('nightly_price', 0):,.0f}/night "
            f"(★{h.get('rating', '?')}) [{h.get('data_type', '?')}]"
        )
    return "\n".join(lines)


def _summarise_budget(budget: dict) -> str:
    if not budget:
        return "No budget analysis available."
    return (
        f"  Estimated total: ₹{budget.get('estimated_total', 0):,.0f}\n"
        f"  User budget: ₹{budget.get('user_budget', 0):,.0f}\n"
        f"  Within budget: {budget.get('within_budget', '?')}"
    )


def _summarise_places(places: list[dict]) -> str:
    if not places:
        return ""
    lines = []
    for p in places:
        cost = f"₹{p.get('est_cost', 0):,}" if p.get("est_cost") else "Free"
        lines.append(f"  - {p['name']} ({p.get('category', '?')}) — {cost}")
    return "\n".join(lines)


# ── Fallback ──────────────────────────────────────────────────────────

def _fallback_itinerary(destination: str, days: int, places: list[dict]) -> str:
    """Generate a basic text itinerary without the LLM."""
    lines = [f"# {days}-Day Trip to {destination}\n"]
    lines.append("_(Generated with basic planner — LLM was unavailable)_\n")

    for day in range(1, days + 1):
        lines.append(f"\n## Day {day}")
        lines.append("09:00 — Breakfast at hotel")
        if places:
            # Pick 2–3 activities per day
            start_idx = ((day - 1) * 3) % len(places)
            for j in range(3):
                idx = (start_idx + j) % len(places)
                p = places[idx]
                hour = 10 + j * 3
                cost_s = f"₹{p.get('est_cost', 0):,}" if p.get("est_cost") else "Free"
                lines.append(f"{hour:02d}:00 — {p['name']} (Est. {cost_s})")
        lines.append("19:00 — Dinner")
        lines.append("21:00 — Return to hotel")

    lines.append("\n\n_All costs are estimated. No bookings have been made._")
    return "\n".join(lines)
