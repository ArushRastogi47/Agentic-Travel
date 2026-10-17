"""
TravelState — the single shared state flowing through the LangGraph graph.

Uses TypedDict with Annotated reducers so that LangGraph correctly
merges partial updates from parallel branches.
"""

from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langgraph.graph import add_messages


def _replace(old: Any, new: Any) -> Any:
    """Simple last-writer-wins reducer."""
    return new


class TravelState(TypedDict, total=False):
    # ── User input ────────────────────────────────────────────────────
    user_query: Annotated[str, _replace]

    # ── Guardrail ─────────────────────────────────────────────────────
    validation_status: Annotated[str, _replace]   # "pass" | "block"
    validation_reason: Annotated[str, _replace]

    # ── Supervisor ────────────────────────────────────────────────────
    trip_constraints: Annotated[dict, _replace]
    selected_agents: Annotated[list[str], _replace]
    supervisor_reasoning: Annotated[str, _replace]

    # ── Specialist results ────────────────────────────────────────────
    flight_results: Annotated[list[dict], _replace]
    hotel_results: Annotated[list[dict], _replace]
    weather_info: Annotated[dict, _replace]
    budget_analysis: Annotated[dict, _replace]
    itinerary_plan: Annotated[str, _replace]

    # ── LLM / message history ────────────────────────────────────────
    messages: Annotated[list, add_messages]
    llm_calls: Annotated[list[dict], _replace]

    # ── Human-in-the-loop ─────────────────────────────────────────────
    human_feedback: Annotated[str, _replace]
    human_decision: Annotated[str, _replace]  # "approve" | "changes" | "pending"

    # ── Final ─────────────────────────────────────────────────────────
    final_response: Annotated[str, _replace]

    # ── Metadata ──────────────────────────────────────────────────────
    iteration: Annotated[int, _replace]
    workflow_status: Annotated[list[str], _replace]  # for UI progress
