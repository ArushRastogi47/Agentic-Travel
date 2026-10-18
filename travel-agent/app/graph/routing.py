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
    Route after supervisor: fan out to selected specialist agents in parallel.
    If no specialists are selected, routes directly to downstream processing.
    """
    selected = state.get("selected_agents", [])
    logger.info(f"[Router] Supervisor selected agents: {selected}")

    agent_map = {
        "flight": "flight_agent",
        "hotel": "hotel_agent",
        "weather": "weather_agent",
    }

    nodes = [agent_map[agent] for agent in selected if agent in agent_map]

    if nodes:
        return nodes

    # If no specialist data-fetchers needed, jump forward
    if "budget" in selected:
        return ["budget_agent"]
    elif "itinerary" in selected:
        return ["itinerary_agent"]
    return ["final_response"]


def after_specialists(
    state: TravelState,
) -> Literal["budget_agent", "itinerary_agent", "final_response"]:
    """Route after parallel specialists converge at join node."""
    selected = state.get("selected_agents", [])
    if "budget" in selected:
        return "budget_agent"
    elif "itinerary" in selected:
        return "itinerary_agent"
    return "final_response"


def after_budget(
    state: TravelState,
) -> Literal["itinerary_agent", "final_response"]:
    """After budget → proceed to itinerary if requested, else final response."""
    selected = state.get("selected_agents", [])
    if "itinerary" in selected:
        return "itinerary_agent"
    return "final_response"


def after_human_review(
    state: TravelState,
) -> Literal["final_response", "supervisor"]:
    """Route based on human decision, with safety guard against infinite loops."""
    decision = state.get("human_decision", "pending")
    iteration = state.get("iteration", 0)

    if decision == "changes":
        if iteration >= 3:
            logger.warning(
                f"[Router] Max iterations ({iteration}) reached — finalizing response"
            )
            return "final_response"
        logger.info(
            f"[Router] Human requested changes (iteration {iteration}) — re-routing to supervisor"
        )
        return "supervisor"
    elif decision == "approve":
        logger.info("[Router] Human approved — generating final response")
        return "final_response"

    # If still pending or unexpected, default to final response
    logger.info("[Router] Decision not 'changes' — routing to final response")
    return "final_response"

