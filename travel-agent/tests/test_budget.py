"""Tests for the budget agent — all deterministic calculations."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agents.budget_agent import budget_agent


class TestBudgetAgent:
    def test_basic_budget_calculation(self):
        state = {
            "trip_constraints": {
                "destination": "Dubai",
                "duration_days": 4,
                "budget": 80000,
                "currency": "INR",
            },
            "flight_results": [
                {"airline": "Test Air", "price": 15000, "data_type": "mock"},
                {"airline": "Test Air 2", "price": 20000, "data_type": "mock"},
            ],
            "hotel_results": [
                {"name": "Test Hotel", "nightly_price": 5000, "data_type": "mock"},
                {"name": "Test Hotel 2", "nightly_price": 8000, "data_type": "mock"},
            ],
            "workflow_status": [],
        }
        result = budget_agent(state)
        budget = result["budget_analysis"]

        assert budget["flights"] == 30000  # cheapest * 2 (round trip)
        assert budget["hotels"] == 15000  # cheapest * 3 nights
        assert budget["estimated_total"] > 0
        assert isinstance(budget["within_budget"], bool)

    def test_within_budget(self):
        state = {
            "trip_constraints": {
                "destination": "Goa",
                "duration_days": 3,
                "budget": 200000,
            },
            "flight_results": [{"price": 5000}],
            "hotel_results": [{"nightly_price": 3000}],
            "workflow_status": [],
        }
        result = budget_agent(state)
        assert result["budget_analysis"]["within_budget"] is True

    def test_over_budget(self):
        state = {
            "trip_constraints": {
                "destination": "Dubai",
                "duration_days": 7,
                "budget": 10000,
            },
            "flight_results": [{"price": 20000}],
            "hotel_results": [{"nightly_price": 8000}],
            "workflow_status": [],
        }
        result = budget_agent(state)
        assert result["budget_analysis"]["within_budget"] is False

    def test_no_budget_specified(self):
        state = {
            "trip_constraints": {
                "destination": "Dubai",
                "duration_days": 4,
                "budget": 0,
            },
            "flight_results": [{"price": 15000}],
            "hotel_results": [{"nightly_price": 5000}],
            "workflow_status": [],
        }
        result = budget_agent(state)
        # Should still calculate total, within_budget defaults to True
        assert result["budget_analysis"]["estimated_total"] > 0
        assert result["budget_analysis"]["within_budget"] is True

    def test_empty_results(self):
        state = {
            "trip_constraints": {
                "destination": "Dubai",
                "duration_days": 4,
                "budget": 80000,
            },
            "flight_results": [],
            "hotel_results": [],
            "workflow_status": [],
        }
        result = budget_agent(state)
        # Should still compute food + transport + activities + misc
        assert result["budget_analysis"]["flights"] == 0
        assert result["budget_analysis"]["hotels"] == 0
        assert result["budget_analysis"]["estimated_total"] > 0
