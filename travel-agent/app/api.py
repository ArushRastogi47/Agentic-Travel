"""
FastAPI backend for the Travel Agent.

Endpoints:
    POST /trip              — Start a new trip planning session
    POST /trip/{id}/resume  — Resume with human feedback
    GET  /trip/{id}         — Get current state
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.graph.graph import build_graph
from app.logging_config import logger
from app.persistence.database import (
    init_database,
    save_conversation,
    save_feedback,
    save_state,
)

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    logger.info("[API] Travel Agent API started")
    yield


app = FastAPI(
    title="LangGraph Travel Agent",
    description="Agentic AI Travel Planner — zero-cost, local-first",
    version="1.0.0",
    lifespan=lifespan,
)

# Build graph once at startup
_graph = build_graph()



# ── Request / Response models ─────────────────────────────────────────

class TripRequest(BaseModel):
    query: str


class ResumeRequest(BaseModel):
    decision: str  # "approve" or "changes"
    feedback: str = ""


class TripResponse(BaseModel):
    thread_id: str
    status: str
    itinerary: Optional[str] = None
    final_response: Optional[str] = None
    workflow_status: list[str] = []
    budget_analysis: Optional[dict] = None
    validation_reason: Optional[str] = None


# ── Endpoints ─────────────────────────────────────────────────────────

@app.post("/trip", response_model=TripResponse)
def create_trip(req: TripRequest):
    """Start a new trip planning session."""
    thread_id = str(uuid.uuid4())[:8]
    logger.info(f"[API] New trip: {thread_id} — {req.query!r}")

    save_conversation(thread_id, req.query)

    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {"user_query": req.query, "iteration": 0}

    try:
        # Run graph until interrupt (human_review)
        result = _graph.invoke(initial_state, config=config)

        if result.get("validation_status") == "block":
            status = "blocked"
        elif result.get("final_response"):
            status = "complete"
        else:
            status = "awaiting_review"


        save_state(thread_id, result)

        return TripResponse(
            thread_id=thread_id,
            status=status,
            itinerary=result.get("itinerary_plan"),
            final_response=result.get("final_response"),
            workflow_status=result.get("workflow_status", []),
            budget_analysis=result.get("budget_analysis"),
            validation_reason=result.get("validation_reason"),
        )


    except Exception as exc:
        logger.error(f"[API] Graph execution failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/trip/{thread_id}/resume", response_model=TripResponse)
def resume_trip(thread_id: str, req: ResumeRequest):
    """Resume after human review."""
    logger.info(f"[API] Resume: {thread_id} — {req.decision}")

    save_feedback(thread_id, req.decision, req.feedback)

    config = {"configurable": {"thread_id": thread_id}}

    try:
        # Update state with human decision
        update = {
            "human_decision": req.decision,
            "human_feedback": req.feedback,
        }
        _graph.update_state(config, update)

        # Continue execution
        result = _graph.invoke(None, config=config)

        status = "complete" if result.get("final_response") else "awaiting_review"

        save_state(thread_id, result)

        return TripResponse(
            thread_id=thread_id,
            status=status,
            itinerary=result.get("itinerary_plan"),
            final_response=result.get("final_response"),
            workflow_status=result.get("workflow_status", []),
            budget_analysis=result.get("budget_analysis"),
        )

    except Exception as exc:
        logger.error(f"[API] Resume failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/trip/{thread_id}", response_model=TripResponse)
def get_trip(thread_id: str):
    """Get current state of a trip."""
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = _graph.get_state(config)

    if not snapshot or not snapshot.values:
        raise HTTPException(status_code=404, detail="Trip not found")

    state = snapshot.values
    status = "blocked" if state.get("validation_status") == "block" else (
        "complete" if state.get("final_response") else "awaiting_review"
    )

    return TripResponse(
        thread_id=thread_id,
        status=status,
        itinerary=state.get("itinerary_plan"),
        final_response=state.get("final_response"),
        workflow_status=state.get("workflow_status", []),
        budget_analysis=state.get("budget_analysis"),
    )
