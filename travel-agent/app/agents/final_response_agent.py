"""
Final Response Agent — produces the polished user-facing travel plan.
Uses the LLM to synthesise all data into a clear summary.
"""

from __future__ import annotations

import json
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from app.graph.state import TravelState
from app.logging_config import logger
from app.tools.llm import get_llm


_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "final_response.txt"


def final_response_agent(state: TravelState) -> dict:
    """LangGraph node — generate the final polished response."""
    logger.info("[Final Response] Generating final travel plan")

    prev_status = state.get("workflow_status", [])

    plan_data = {
        "trip_constraints": state.get("trip_constraints", {}),
        "itinerary": state.get("itinerary_plan", ""),
        "budget_analysis": state.get("budget_analysis", {}),
        "flights": state.get("flight_results", [])[:3],
        "hotels": state.get("hotel_results", [])[:3],
        "weather": state.get("weather_info", {}),
    }

    try:
        prompt_template = _PROMPT_PATH.read_text()
        prompt = prompt_template.format(plan_data=json.dumps(plan_data, indent=2, default=str))

        llm = get_llm(temperature=0.4)
        response = llm.invoke([
            SystemMessage(content="You are a helpful travel planning assistant."),
            HumanMessage(content=prompt),
        ])

        final = response.content
        logger.info("[Final Response] Generated successfully")

        return {
            "final_response": final,
            "workflow_status": prev_status + ["✅ Final plan ready"],
        }

    except Exception as exc:
        logger.error(f"[Final Response] LLM failed: {exc}")
        # Fallback: just use the raw itinerary
        itinerary = state.get("itinerary_plan", "No itinerary available.")
        budget = state.get("budget_analysis", {})

        fallback = (
            "# Your Travel Plan\n\n"
            f"{itinerary}\n\n"
            "## Budget Summary\n"
            f"- Estimated total: ₹{budget.get('estimated_total', 'N/A'):,}\n"
            f"- User budget: ₹{budget.get('user_budget', 'N/A'):,}\n"
            f"- Within budget: {budget.get('within_budget', 'N/A')}\n\n"
            "_All prices are estimated. No bookings have been made._"
        )
        return {
            "final_response": fallback,
            "workflow_status": prev_status + ["⚠️ Final plan ready (basic format)"],
        }
