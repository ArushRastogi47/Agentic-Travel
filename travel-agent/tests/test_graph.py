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
