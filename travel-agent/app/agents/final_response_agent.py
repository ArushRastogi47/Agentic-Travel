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
        if isinstance(final, list):
            final = "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in final)
        elif not isinstance(final, str):
            final = str(final)

        logger.info("[Final Response] Generated successfully")

        return {
            "final_response": final,
            "workflow_status": ["✅ Final plan ready"],
        }

    except Exception as exc:
        logger.error(f"[Final Response] LLM failed: {exc}")
        # Fallback: synthesize state data cleanly
        itinerary = state.get("itinerary_plan", "")
        budget = state.get("budget_analysis", {})
        weather = state.get("weather_info", {})

        fallback_parts = ["# Your Travel Plan\n"]
        if itinerary:
            fallback_parts.append(itinerary)
            fallback_parts.append("\n")

        if weather and weather.get("daily"):
            fallback_parts.append("## Weather Forecast")
            for day in weather["daily"][:5]:
                fallback_parts.append(
                    f"- **{day.get('date', '')}**: {day.get('description', '')}, High: {day.get('temperature_high', '')}°C, Low: {day.get('temperature_low', '')}°C"
                )
            fallback_parts.append("\n")

        if budget:
            est = budget.get("estimated_total", 0)
            ub = budget.get("user_budget", 0)
            fallback_parts.append("## Budget Summary")
            fallback_parts.append(f"- Estimated total: ₹{est:,.0f}" if isinstance(est, (int, float)) else f"- Estimated total: {est}")
            if ub:
                fallback_parts.append(f"- User budget: ₹{ub:,.0f}" if isinstance(ub, (int, float)) else f"- User budget: {ub}")
            fallback_parts.append(f"- Within budget: {budget.get('within_budget', True)}\n")

        fallback_parts.append("_All prices are estimated. No bookings have been made._")
        fallback = "\n".join(fallback_parts)

        return {
            "final_response": fallback,
            "workflow_status": ["⚠️ Final plan ready (basic format)"],
        }

