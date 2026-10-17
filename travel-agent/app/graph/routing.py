"""
Routing logic — conditional edges for the LangGraph graph.

These functions determine which node to execute next based on the
current state.
"""

from __future__ import annotations

from typing import Literal

from app.graph.state import TravelState
from app.logging_config import logger


def after_guardrail(state: TravelState) -> Literal["supervisor", "end"]:
    """Route after guardrail: continue or stop."""
    if state.get("validation_status") == "block":
        logger.info("[Router] Guardrail blocked — ending graph")
        return "end"
    return "supervisor"


def after_supervisor(state: TravelState) -> list[str]:
    """
    Route after supervisor: fan out to selected specialist agents.
    Returns a list of Send objects for parallel execution.
    """
    selected = state.get("selected_agents", [])
    logger.info(f"[Router] Supervisor selected: {selected}")

    # Map agent names → node names
    agent_map = {
        "flight": "flight_agent",
        "hotel": "hotel_agent",
        "weather": "weather_agent",
    }

    nodes = []
    for agent in selected:
        if agent in agent_map:
            nodes.append(agent_map[agent])

    if not nodes:
        # At least run weather as a default
        nodes.append("weather_agent")

    return nodes


def after_specialists(state: TravelState) -> Literal["budget_agent", "itinerary_agent"]:
    """Route after parallel specialists converge."""
    selected = state.get("selected_agents", [])
    if "budget" in selected:
        return "budget_agent"
    return "itinerary_agent"


def after_budget(state: TravelState) -> Literal["itinerary_agent"]:
    """After budget → always go to itinerary."""
    return "itinerary_agent"


def after_human_review(
    state: TravelState,
) -> Literal["final_response", "supervisor"]:
    """Route based on human decision."""
    decision = state.get("human_decision", "pending")
    if decision == "approve":
        logger.info("[Router] Human approved — generating final response")
        return "final_response"
    elif decision == "changes":
        logger.info("[Router] Human requested changes — re-routing to supervisor")
        return "supervisor"
    # If still pending, we shouldn't be here — but default to waiting
    logger.warning("[Router] Unexpected state in after_human_review")
    return "final_response"
