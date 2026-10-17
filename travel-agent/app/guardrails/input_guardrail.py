"""
Input Guardrail — validates the user request before any agent execution.

Uses a mix of keyword heuristics (fast, deterministic) and optionally
the LLM for ambiguous cases.
"""

from __future__ import annotations

import re
from datetime import datetime

from app.graph.state import TravelState
from app.logging_config import logger
from app.models.schemas import GuardrailResult


# ── Blocked patterns ──────────────────────────────────────────────────

_BLOCKED_KEYWORDS = [
    "hack", "exploit", "steal", "illegal", "drug", "weapon",
    "bomb", "attack", "fraud", "fake passport", "smuggle",
    "launder", "counterfeit",
]

_TRAVEL_KEYWORDS = [
    "trip", "travel", "visit", "plan", "tour", "vacation",
    "holiday", "flight", "hotel", "weather", "itinerary",
    "destination", "go to", "fly to", "stay in", "book",
    "budget", "cheap", "expensive", "day trip", "weekend",
]


def validate_input(state: TravelState) -> dict:
    """
    Guardrail node for the LangGraph graph.

    Returns a partial state update with validation_status and
    validation_reason.
    """
    query = state.get("user_query", "").strip()
    logger.info(f"[Guardrail] Validating: {query!r}")

    result = _check(query)

    status = "pass" if result.allowed else "block"
    logger.info(f"[Guardrail] Result: {status} — {result.reason}")

    update: dict = {
        "validation_status": status,
        "validation_reason": result.reason,
        "workflow_status": [f"{'✅' if result.allowed else '❌'} Request validated"],
    }
    if result.allowed:
        update["user_query"] = result.normalized_request or query
    return update


def _check(query: str) -> GuardrailResult:
    # 1. Empty check
    if not query:
        return GuardrailResult(
            allowed=False,
            reason="No travel request provided.",
        )

    q_lower = query.lower()

    # 2. Safety check
    for kw in _BLOCKED_KEYWORDS:
        if kw in q_lower:
            return GuardrailResult(
                allowed=False,
                reason="The request is outside the supported travel-planning scope.",
            )

    # 3. Travel-relevance check
    is_travel = any(kw in q_lower for kw in _TRAVEL_KEYWORDS)
    # Also allow if it mentions a place-like pattern (e.g., "Dubai", "to Paris")
    has_destination = bool(re.search(r"\bto\s+[A-Z]", query))
    if not is_travel and not has_destination:
        return GuardrailResult(
            allowed=False,
            reason="This doesn't appear to be a travel-planning request. "
                   "Please describe where you'd like to travel.",
        )

    # 4. Minimum specificity
    if len(query.split()) < 3:
        return GuardrailResult(
            allowed=False,
            reason="Please provide more details — at least a destination "
                   "and rough duration or dates.",
        )

    # ── Passed ─────────────────────────────────────────────────────
    return GuardrailResult(
        allowed=True,
        reason="Valid travel planning request.",
        normalized_request=query.strip(),
    )
