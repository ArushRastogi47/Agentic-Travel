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
        state = {"human_decision": "changes", "iteration": 1}
        assert after_human_review(state) == "supervisor"

    def test_changes_max_iterations_routes_to_final(self):
        state = {"human_decision": "changes", "iteration": 3}
        assert after_human_review(state) == "final_response"

    def test_pending_defaults_to_final(self):
        state = {"human_decision": "pending"}
        assert after_human_review(state) == "final_response"

    def test_full_change_and_approval_cycle(self):
        import uuid
        from app.graph.graph import build_graph

        graph = build_graph()
        thread_id = f"test-e2e-{uuid.uuid4().hex[:8]}"
        config = {"configurable": {"thread_id": thread_id}}

        # Run up to interrupt
        for _ in graph.stream({"user_query": "Plan 3 days in Goa under 25000"}, config=config):
            pass


        snap1 = graph.get_state(config)
        assert snap1.next == ("human_review",)
        assert snap1.values.get("iteration") == 1

        # Request changes
        graph.update_state(config, {"human_decision": "changes", "human_feedback": "Cheaper hotel please"})
        for _ in graph.stream(None, config=config):
            pass

        snap2 = graph.get_state(config)
        assert snap2.values.get("iteration") >= 2

        if snap2.next == ("human_review",):
            # Approve
            graph.update_state(config, {"human_decision": "approve"})
            final = graph.invoke(None, config=config)
        else:
            final = snap2.values

        assert final.get("final_response") != ""



