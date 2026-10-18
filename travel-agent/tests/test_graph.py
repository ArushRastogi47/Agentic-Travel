"""Tests for the complete LangGraph graph (mock/demo mode)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Force demo mode for tests
import os
os.environ["DEMO_MODE"] = "true"

from app.graph.graph import build_graph


class TestGraph:
    def test_blocked_request(self):
        """Blocked requests should terminate cleanly."""
        graph = build_graph()
        config = {"configurable": {"thread_id": "test-blocked"}}
        result = graph.invoke(
            {"user_query": "Help me hack an airline", "iteration": 0},
            config=config,
        )
        assert result.get("validation_status") == "block"

    def test_empty_request(self):
        """Empty requests should be blocked."""
        graph = build_graph()
        config = {"configurable": {"thread_id": "test-empty"}}
        result = graph.invoke(
            {"user_query": "", "iteration": 0},
            config=config,
        )
        assert result.get("validation_status") == "block"

    def test_weather_only_routing(self):
        """Weather-only query should route through weather and straight to final response."""
        graph = build_graph()
        config = {"configurable": {"thread_id": "test-weather-only"}}
        result = graph.invoke(
            {"user_query": "What is the weather in Goa?"},
            config=config,
        )
        assert result.get("validation_status") == "pass"
        assert "weather" in result.get("selected_agents", [])
        assert "flight" not in result.get("selected_agents", [])
        assert result.get("weather_info", {}) != {}
        # Flight and hotel should NOT have run
        assert result.get("flight_results") is None or result.get("flight_results") == []
        assert result.get("hotel_results") is None or result.get("hotel_results") == []
        # Final response should be populated
        assert result.get("final_response") != ""

    def test_full_trip_execution_reaches_interrupt(self):
        """Full trip request should run specialists, join, calculate budget, and interrupt for human review."""
        graph = build_graph()
        config = {"configurable": {"thread_id": "test-trip-interrupt"}}
        
        # Stream until interrupt
        nodes_executed = []
        for event in graph.stream(
            {"user_query": "Plan a 4-day trip to Dubai under 80000"},
            config=config,
        ):
            nodes_executed.extend(list(event.keys()))

        assert "guardrail" in nodes_executed
        assert "supervisor" in nodes_executed
        assert "flight_agent" in nodes_executed
        assert "hotel_agent" in nodes_executed
        assert "weather_agent" in nodes_executed
        assert "join_specialists" in nodes_executed
        assert "budget_agent" in nodes_executed
        assert "itinerary_agent" in nodes_executed
        assert "__interrupt__" in nodes_executed

        # Verify budget ran exactly once
        assert nodes_executed.count("budget_agent") == 1

