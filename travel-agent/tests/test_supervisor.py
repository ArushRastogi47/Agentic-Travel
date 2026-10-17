"""Tests for the supervisor agent — heuristic fallback path."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agents.supervisor import _heuristic_route, _extract_constraints_heuristic


class TestSupervisorHeuristic:
    def test_full_trip_request(self):
        result = _heuristic_route("Plan a 4 day trip to Dubai next month under ₹80000")
        assert "flight" in result.selected_agents
        assert "hotel" in result.selected_agents
        assert "weather" in result.selected_agents
        assert "budget" in result.selected_agents
        assert "itinerary" in result.selected_agents

    def test_weather_only(self):
        result = _heuristic_route("What's the weather like in Dubai next week?")
        assert result.selected_agents == ["weather"]

    def test_climate_query(self):
        result = _heuristic_route("What is the climate in Tokyo in December?")
        assert result.selected_agents == ["weather"]

    def test_destination_extraction(self):
        constraints = _extract_constraints_heuristic("Plan a trip to Paris for 5 days")
        assert constraints.destination.lower() == "paris"
        assert constraints.duration_days == 5

    def test_budget_extraction(self):
        constraints = _extract_constraints_heuristic("Trip to Dubai under 80000")
        assert constraints.budget == 80000

    def test_duration_extraction(self):
        constraints = _extract_constraints_heuristic("Plan a 3 day trip to Goa")
        assert constraints.duration_days == 3

    def test_next_month_dates(self):
        constraints = _extract_constraints_heuristic("Trip to Dubai next month for 4 days")
        assert constraints.start_date != ""
        assert constraints.end_date != ""
