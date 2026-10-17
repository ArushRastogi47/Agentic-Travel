"""
LangGraph graph definition — the complete travel-planning workflow.

    START → guardrail → supervisor → [flight, hotel, weather] (parallel)
          → budget → itinerary → human_review
          → approve → final_response → END
          → changes → supervisor (loop back)
"""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    budget_node,
    final_response_node,
    flight_node,
    guardrail_node,
    hotel_node,
    human_review_node,
    itinerary_node,
    supervisor_node,
    weather_node,
)
from app.graph.routing import (
    after_budget,
    after_guardrail,
    after_human_review,
    after_specialists,
)
from app.graph.state import TravelState
from app.logging_config import logger


def build_graph(checkpointer=None):
    """
    Construct and compile the LangGraph StateGraph.

    Returns a compiled graph that can be invoked or streamed.
    """
    logger.info("[Graph] Building travel agent graph...")

    builder = StateGraph(TravelState)

    # ── Add nodes ──────────────────────────────────────────────────
    builder.add_node("guardrail", guardrail_node)
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("flight_agent", flight_node)
    builder.add_node("hotel_agent", hotel_node)
    builder.add_node("weather_agent", weather_node)
    builder.add_node("budget_agent", budget_node)
    builder.add_node("itinerary_agent", itinerary_node)
    builder.add_node("human_review", human_review_node)
    builder.add_node("final_response", final_response_node)

    # ── Edges ──────────────────────────────────────────────────────

    # START → guardrail
    builder.add_edge(START, "guardrail")

    # guardrail → supervisor | END
    builder.add_conditional_edges(
        "guardrail",
        after_guardrail,
        {"supervisor": "supervisor", "end": END},
    )

    # supervisor → parallel specialists
    # We use conditional edges to dynamically select which specialists run.
    # For simplicity in LangGraph, we route through all three but each
    # checks if it was selected.
    builder.add_edge("supervisor", "flight_agent")
    builder.add_edge("supervisor", "hotel_agent")
    builder.add_edge("supervisor", "weather_agent")

    # All specialists → budget
    builder.add_edge("flight_agent", "budget_agent")
    builder.add_edge("hotel_agent", "budget_agent")
    builder.add_edge("weather_agent", "budget_agent")

    # budget → itinerary
    builder.add_edge("budget_agent", "itinerary_agent")

    # itinerary → human review (interrupt)
    builder.add_edge("itinerary_agent", "human_review")

    # human review → final_response | supervisor (loop)
    builder.add_conditional_edges(
        "human_review",
        after_human_review,
        {
            "final_response": "final_response",
            "supervisor": "supervisor",
        },
    )

    # final response → END
    builder.add_edge("final_response", END)

    # ── Compile ────────────────────────────────────────────────────
    if checkpointer is None:
        checkpointer = MemorySaver()

    graph = builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["human_review"],  # pause for human decision
    )

    logger.info("[Graph] Compiled successfully")
    return graph
