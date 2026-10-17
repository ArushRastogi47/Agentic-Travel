"""Tests for human-in-the-loop flow."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.graph.routing import after_human_review


class TestHumanLoop:
    def test_approve_routes_to_final(self):
        state = {"human_decision": "approve"}
        assert after_human_review(state) == "final_response"

    def test_changes_routes_to_supervisor(self):
        state = {"human_decision": "changes"}
        assert after_human_review(state) == "supervisor"

    def test_pending_defaults_to_final(self):
        state = {"human_decision": "pending"}
        assert after_human_review(state) == "final_response"
