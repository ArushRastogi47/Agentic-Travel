"""
Graph node wrappers — thin wrappers that LangGraph calls directly.
Each delegates to the actual agent implementation.

The human_review node is an interrupt point for human-in-the-loop.
"""

from __future__ import annotations

from app.agents.budget_agent import budget_agent
from app.agents.final_response_agent import final_response_agent
from app.agents.flight_agent import flight_agent
from app.agents.hotel_agent import hotel_agent
from app.agents.itinerary_agent import itinerary_agent
from app.agents.supervisor import supervisor_agent
from app.agents.weather_agent import weather_agent
from app.graph.state import TravelState
from app.guardrails.input_guardrail import validate_input
from app.logging_config import logger


def guardrail_node(state: TravelState) -> dict:
    return validate_input(state)


def supervisor_node(state: TravelState) -> dict:
    return supervisor_agent(state)


def flight_node(state: TravelState) -> dict:
    return flight_agent(state)


def hotel_node(state: TravelState) -> dict:
    return hotel_agent(state)


def weather_node(state: TravelState) -> dict:
    return weather_agent(state)


def join_specialists_node(state: TravelState) -> dict:
    """Sync barrier where parallel specialist branches merge."""
    logger.info("[Join] Parallel specialists merged")
    return {}


def budget_node(state: TravelState) -> dict:
    return budget_agent(state)



def itinerary_node(state: TravelState) -> dict:
    return itinerary_agent(state)


def human_review_node(state: TravelState) -> dict:
    """
    Interrupt point.  The graph pauses here and waits for
    human_decision to be set to 'approve' or 'changes'.
    """
    logger.info("[Human Review] Awaiting user decision...")
    return {
        "human_decision": state.get("human_decision", "pending"),
    }


def final_response_node(state: TravelState) -> dict:
    return final_response_agent(state)
