"""Tests for the FastAPI backend."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["DEMO_MODE"] = "true"

from fastapi.testclient import TestClient
from app.api import app

client = TestClient(app)


def test_create_trip_blocked():
    response = client.post("/trip", json={"query": "Help me hack an airline database"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "blocked"
    assert data["validation_reason"] is not None


def test_create_trip_weather_direct():
    response = client.post("/trip", json={"query": "What is the weather in Goa?"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "complete"
    assert data["final_response"] is not None


def test_create_and_resume_trip():
    # 1. Start full trip planning session
    response = client.post("/trip", json={"query": "Plan 3 days in Goa under 20000"})
    assert response.status_code == 200
    data = response.json()
    thread_id = data["thread_id"]
    assert data["status"] == "awaiting_review"
    assert data["itinerary"] is not None

    # 2. Get state
    get_res = client.get(f"/trip/{thread_id}")
    assert get_res.status_code == 200
    assert get_res.json()["thread_id"] == thread_id

    # 3. Resume with approval
    resume_res = client.post(
        f"/trip/{thread_id}/resume",
        json={"decision": "approve", "feedback": ""},
    )
    assert resume_res.status_code == 200
    res_data = resume_res.json()
    assert res_data["status"] == "complete"
    assert res_data["final_response"] is not None
