"""
LangGraph graph definition — the complete travel-planning workflow.

    START → guardrail → supervisor → [flight, hotel, weather] (parallel)
          → budget → itinerary → human_review
          → approve → final_response → END
          → changes → supervisor (loop back)
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

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
    join_specialists_node,
    supervisor_node,
    weather_node,
)
from app.graph.routing import (
    after_budget,
    after_guardrail,
    after_human_review,
    after_specialists,
    after_supervisor,
)
from app.graph.state import TravelState
from app.logging_config import logger
from app.persistence.database import _get_db_path


def get_default_checkpointer():
    """Returns a persistent SqliteSaver, or MemorySaver as fallback."""
    try:
        from langgraph.checkpoint.sqlite import SqliteSaver

        db_path = _get_db_path()
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(db_path, check_same_thread=False)
        saver = SqliteSaver(conn)
        saver.setup()
        return saver
    except Exception as exc:
        logger.warning(
            f"[Graph] Could not initialize SqliteSaver ({exc}), using MemorySaver"
        )
        return MemorySaver()


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
    builder.add_node("join_specialists", join_specialists_node)
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

    # supervisor → dynamic fan-out to specialists (or jump forward)
    builder.add_conditional_edges(
        "supervisor",
        after_supervisor,
        [
            "flight_agent",
            "hotel_agent",
            "weather_agent",
            "budget_agent",
            "itinerary_agent",
            "final_response",
        ],
    )

    # All parallel specialists converge at join node
    builder.add_edge("flight_agent", "join_specialists")
    builder.add_edge("hotel_agent", "join_specialists")
    builder.add_edge("weather_agent", "join_specialists")

    # join_specialists → budget | itinerary | final_response
    builder.add_conditional_edges(
        "join_specialists",
        after_specialists,
        {
            "budget_agent": "budget_agent",
            "itinerary_agent": "itinerary_agent",
            "final_response": "final_response",
        },
    )

    # budget → itinerary | final_response
    builder.add_conditional_edges(
        "budget_agent",
        after_budget,
        {
            "itinerary_agent": "itinerary_agent",
            "final_response": "final_response",
        },
    )

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
        checkpointer = get_default_checkpointer()

    graph = builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["human_review"],  # pause for human decision
    )

    logger.info("[Graph] Compiled successfully")
    return graph

