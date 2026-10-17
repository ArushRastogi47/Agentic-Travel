"""
Supervisor Agent — the orchestrator.

Decides which specialist agents are needed based on the user's request,
and extracts trip constraints using the local LLM.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from app.graph.state import TravelState
from app.logging_config import logger
from app.models.schemas import SupervisorOutput, TripConstraints
from app.tools.llm import get_llm


_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "supervisor.txt"


def supervisor_agent(state: TravelState) -> dict:
    """
    LangGraph node.  Uses the LLM to understand intent and select agents.
    Falls back to heuristics if the LLM is unavailable.
    """
    query = state.get("user_query", "")
    logger.info(f"[Supervisor] Analysing: {query!r}")

    try:
        result = _llm_route(query)
    except Exception as exc:
        logger.warning(f"[Supervisor] LLM failed ({exc}), using heuristic fallback")
        result = _heuristic_route(query)

    logger.info(f"[Supervisor] Selected agents: {result.selected_agents}")

    prev_status = state.get("workflow_status", [])
    return {
        "selected_agents": result.selected_agents,
        "trip_constraints": result.trip_constraints.model_dump(),
        "supervisor_reasoning": result.reasoning,
        "workflow_status": prev_status + ["✅ Supervisor selected agents"],
        "iteration": state.get("iteration", 0) + 1,
    }


# ── LLM-based routing ────────────────────────────────────────────────

def _llm_route(query: str) -> SupervisorOutput:
    system_prompt = _PROMPT_PATH.read_text()

    today = datetime.now().strftime("%Y-%m-%d")
    user_msg = (
        f"Today's date is {today}.\n\n"
        f"User request: {query}"
    )

    llm = get_llm(temperature=0.1)
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_msg),
    ])

    raw = response.content
    # Extract JSON from the response (handles markdown code fences)
    json_match = re.search(r"\{[\s\S]*\}", raw)
    if not json_match:
        raise ValueError(f"No JSON found in LLM response: {raw[:200]}")

    data = json.loads(json_match.group())
    constraints = TripConstraints(**data.get("trip_constraints", {}))
    return SupervisorOutput(
        selected_agents=data.get("selected_agents", []),
        trip_constraints=constraints,
        reasoning=data.get("reasoning", ""),
    )


# ── Heuristic fallback ──────────────────────────────────────────────

def _heuristic_route(query: str) -> SupervisorOutput:
    """Simple keyword-based agent selection when LLM is unavailable."""
    q = query.lower()
    agents: list[str] = []

    # Always try to extract destination
    constraints = _extract_constraints_heuristic(query)

    # Weather-only check
    weather_only = (
        ("weather" in q or "climate" in q or "temperature" in q)
        and "trip" not in q and "plan" not in q and "travel" not in q
    )
    if weather_only:
        return SupervisorOutput(
            selected_agents=["weather"],
            trip_constraints=constraints,
            reasoning="User asked only about weather.",
        )

    # Full trip planning
    if any(w in q for w in ["flight", "fly", "air"]):
        agents.append("flight")
    else:
        agents.append("flight")  # default for trips

    if any(w in q for w in ["hotel", "stay", "accommodation", "lodge"]):
        agents.append("hotel")
    else:
        agents.append("hotel")

    agents.append("weather")

    if any(w in q for w in ["budget", "cost", "cheap", "₹", "rs", "inr", "under"]):
        agents.append("budget")
    else:
        agents.append("budget")

    agents.append("itinerary")

    return SupervisorOutput(
        selected_agents=list(dict.fromkeys(agents)),  # dedupe, preserve order
        trip_constraints=constraints,
        reasoning="Heuristic fallback — selected standard trip-planning agents.",
    )


def _extract_constraints_heuristic(query: str) -> TripConstraints:
    """Best-effort extraction without an LLM."""
    q = query.lower()

    # Destination: look for "to <Place>"
    dest_match = re.search(r"\bto\s+([A-Za-z\s]+?)(?:\s+(?:for|in|on|next|under|from|within|budget)|[,.]|$)", query, re.IGNORECASE)
    destination = dest_match.group(1).strip().title() if dest_match else ""

    # Duration: "N day(s)"
    dur_match = re.search(r"(\d+)\s*(?:day|night)", q)
    duration = int(dur_match.group(1)) if dur_match else 4

    # Budget: look for numbers near ₹ or INR or "under"
    budget_match = re.search(r"[₹rs.\s]*(\d[\d,]*)", q)
    budget = 0.0
    if budget_match:
        budget = float(budget_match.group(1).replace(",", ""))
        if budget < 1000:  # probably not a budget
            budget = 0.0

    # Dates: "next month", "next week", specific date
    start_date = ""
    end_date = ""
    today = datetime.now()
    if "next month" in q:
        first_of_next = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
        start_date = first_of_next.strftime("%Y-%m-%d")
        end_date = (first_of_next + timedelta(days=duration - 1)).strftime("%Y-%m-%d")
    elif "next week" in q:
        next_mon = today + timedelta(days=(7 - today.weekday()))
        start_date = next_mon.strftime("%Y-%m-%d")
        end_date = (next_mon + timedelta(days=duration - 1)).strftime("%Y-%m-%d")
    else:
        start_date = (today + timedelta(days=7)).strftime("%Y-%m-%d")
        end_date = (today + timedelta(days=7 + duration - 1)).strftime("%Y-%m-%d")

    return TripConstraints(
        destination=destination,
        duration_days=duration,
        start_date=start_date,
        end_date=end_date,
        budget=budget,
    )
