"""Tests for native model tool calling definitions."""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["DEMO_MODE"] = "true"

from app.tools.agent_tools import (
    ALL_TRAVEL_TOOLS,
    calculate_trip_budget,
    get_destination_attractions,
    get_weather_forecast,
    search_flights,
    search_hotels,
)


def test_tool_count_and_signatures():
    assert len(ALL_TRAVEL_TOOLS) == 5
    tool_names = [t.name for t in ALL_TRAVEL_TOOLS]
    assert "search_flights" in tool_names
    assert "search_hotels" in tool_names
    assert "get_weather_forecast" in tool_names
    assert "get_destination_attractions" in tool_names
    assert "calculate_trip_budget" in tool_names


def test_search_flights_tool():
    res = search_flights.invoke({
        "origin": "Delhi",
        "destination": "Goa",
        "date": "2026-11-01",
        "travelers": 2,
    })
    data = json.loads(res)
    assert isinstance(data, list)
    assert len(data) > 0
    assert "price" in data[0]


def test_search_hotels_tool():
    res = search_hotels.invoke({
        "destination": "Goa",
        "check_in": "2026-11-01",
        "check_out": "2026-11-04",
        "nights": 3,
    })
    data = json.loads(res)
    assert isinstance(data, list)
    assert len(data) > 0
    assert "nightly_price" in data[0]


def test_get_weather_forecast_tool():
    res = get_weather_forecast.invoke({
        "destination": "Goa",
        "start_date": "2026-11-01",
        "end_date": "2026-11-04",
    })
    data = json.loads(res)
    assert "daily" in data
    assert len(data["daily"]) > 0


def test_calculate_trip_budget_tool():
    res = calculate_trip_budget.invoke({
        "destination": "Goa",
        "duration_days": 4,
        "user_budget": 30000,
        "flight_price": 5000,
        "hotel_nightly_price": 3000,
    })
    data = json.loads(res)
    assert data["estimated_total"] > 0
    assert "within_budget" in data
