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


def _merge_status(old: list[str] | None, new: list[str] | None) -> list[str]:
    """
    Reducer that appends status messages from parallel agents,
    and supports resetting status on new iterations using '__RESET__'.
    """
    if not old:
        return [item for item in (new or []) if item != "__RESET__"]
    if not new:
        return old
    if new and new[0] == "__RESET__":
        return [item for item in new[1:] if item != "__RESET__"]
    return old + [item for item in new if item != "__RESET__"]


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
    workflow_status: Annotated[list[str], _merge_status]  # for UI progress
