"""
Streamlit UI for the LangGraph Travel Agent.

Provides:
- Travel query input
- Workflow status tracking
- Itinerary display
- Human-in-the-loop approval / change requests
- Final plan display
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path for imports
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import streamlit as st

from app.graph.graph import build_graph
from app.logging_config import logger
from app.persistence.database import (
    init_database,
    save_conversation,
    save_feedback,
    save_state,
)

# ── Page config ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="✈️ AI Travel Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(120deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .status-item {
        padding: 0.3rem 0;
        font-size: 1rem;
    }
    .itinerary-box {
        background: #1e1e2e;
        border-radius: 10px;
        padding: 1.5rem;
        border: 1px solid #333;
    }
    .budget-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 1.5rem;
        color: white;
    }
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# ── Init ───────────────────────────────────────────────────────────────

def init():
    """Initialise session state and database."""
    init_database()

    if "graph" not in st.session_state:
        st.session_state.graph = build_graph()
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = None
    if "state" not in st.session_state:
        st.session_state.state = None
    if "phase" not in st.session_state:
        st.session_state.phase = "input"  # input | review | complete | blocked


init()


# ── Sidebar ────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚙️ Settings")

    from app.config import DEMO_MODE, OLLAMA_MODEL
    st.info(f"**Model:** {OLLAMA_MODEL}")
    st.info(f"**Demo Mode:** {'✅ ON' if DEMO_MODE else '❌ OFF'}")

    if st.button("🔄 New Trip", use_container_width=True):
        st.session_state.thread_id = None
        st.session_state.state = None
        st.session_state.phase = "input"
        st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Workflow Status")
    if st.session_state.state:
        statuses = st.session_state.state.get("workflow_status", [])
        for s in statuses:
            st.markdown(f"<div class='status-item'>{s}</div>", unsafe_allow_html=True)
    else:
        st.markdown("_No active trip_")

    st.markdown("---")
    st.caption("Built with LangGraph + Ollama • Zero-cost")


# ── Main content ───────────────────────────────────────────────────────

st.markdown("<h1 class='main-header'>✈️ AI Travel Planner</h1>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align: center; color: #888;'>"
    "Powered by LangGraph • Local LLM • Free & Open Source"
    "</p>",
    unsafe_allow_html=True,
)

# ── Phase: Input ───────────────────────────────────────────────────────
if st.session_state.phase == "input":
    st.markdown("### 🌍 Where do you want to travel?")

    query = st.text_area(
        "Describe your trip",
        placeholder="Plan a 4 day trip to Dubai next month under ₹80,000",
        height=100,
        label_visibility="collapsed",
    )

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        plan_btn = st.button(
            "🚀 Plan My Trip",
            use_container_width=True,
            type="primary",
        )

    if plan_btn and query.strip():
        import uuid

        thread_id = str(uuid.uuid4())[:8]
        st.session_state.thread_id = thread_id

        save_conversation(thread_id, query)

        config = {"configurable": {"thread_id": thread_id}}
        initial_state = {"user_query": query, "iteration": 0}

        with st.spinner("🔄 Planning your trip... This may take a moment."):
            try:
                graph = st.session_state.graph
                # Run until interrupt
                for event in graph.stream(initial_state, config=config, stream_mode="updates"):
                    pass  # process events

                # Get final state
                snapshot = graph.get_state(config)
                state = snapshot.values if snapshot else {}
                st.session_state.state = state

                if state.get("validation_status") == "block":
                    st.session_state.phase = "blocked"
                else:
                    st.session_state.phase = "review"

                save_state(thread_id, state)
                st.rerun()

            except Exception as exc:
                st.error(f"❌ Error: {exc}")
                logger.error(f"[UI] Graph failed: {exc}", exc_info=True)

# ── Phase: Blocked ─────────────────────────────────────────────────────
elif st.session_state.phase == "blocked":
    state = st.session_state.state or {}
    st.error(f"❌ **Request Blocked**")
    st.warning(state.get("validation_reason", "Unknown reason"))
    st.info("Please try a different travel-related request.")

    if st.button("↩️ Try Again"):
        st.session_state.phase = "input"
        st.session_state.state = None
        st.rerun()

# ── Phase: Review ──────────────────────────────────────────────────────
elif st.session_state.phase == "review":
    state = st.session_state.state or {}

    # ── Budget Summary ─────────────────────────────────────────────
    budget = state.get("budget_analysis", {})
    if budget:
        st.markdown("### 💰 Budget Summary")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Estimated Total", f"₹{budget.get('estimated_total', 0):,.0f}")
        with col2:
            st.metric("User Budget", f"₹{budget.get('user_budget', 0):,.0f}")
        with col3:
            remaining = budget.get("remaining_budget", 0)
            st.metric("Remaining", f"₹{remaining:,.0f}",
                       delta=f"{'Within' if budget.get('within_budget') else 'Over'} budget")
        with col4:
            st.metric("Status", "✅ OK" if budget.get("within_budget") else "⚠️ Over Budget")

    # ── Itinerary ──────────────────────────────────────────────────
    itinerary = state.get("itinerary_plan", "")
    if itinerary:
        st.markdown("### 📋 Generated Itinerary")
        st.markdown(itinerary)

    # ── Flight & Hotel Results ─────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        flights = state.get("flight_results", [])
        if flights:
            st.markdown("### ✈️ Flight Options")
            for i, f in enumerate(flights[:3], 1):
                with st.expander(f"Option {i}: {f.get('airline', '?')} — ₹{f.get('price', 0):,.0f}"):
                    st.write(f"**Route:** {f.get('origin', '?')} → {f.get('destination', '?')}")
                    st.write(f"**Duration:** {f.get('duration_minutes', 0)} min")
                    st.write(f"**Data:** {f.get('data_type', 'unknown')}")

    with col_right:
        hotels = state.get("hotel_results", [])
        if hotels:
            st.markdown("### 🏨 Hotel Options")
            for i, h in enumerate(hotels[:3], 1):
                with st.expander(f"Option {i}: {h.get('name', '?')} — ₹{h.get('nightly_price', 0):,.0f}/night"):
                    st.write(f"**Rating:** ★ {h.get('rating', '?')}")
                    st.write(f"**Total:** ₹{h.get('total_price', 0):,.0f}")
                    st.write(f"**Amenities:** {', '.join(h.get('amenities', []))}")
                    st.write(f"**Data:** {h.get('data_type', 'unknown')}")

    # ── Weather ────────────────────────────────────────────────────
    weather = state.get("weather_info", {})
    if weather and weather.get("daily"):
        st.markdown("### 🌤️ Weather Forecast")
        cols = st.columns(min(len(weather["daily"]), 7))
        for i, day in enumerate(weather["daily"][:7]):
            with cols[i]:
                st.markdown(f"**{day.get('date', '?')[5:]}**")
                st.markdown(f"☀️ {day.get('temperature_high', '?')}°")
                st.markdown(f"🌙 {day.get('temperature_low', '?')}°")
                st.markdown(f"🌧️ {day.get('rain_probability', 0):.0f}%")

    # ── Approval Buttons ──────────────────────────────────────────
    st.markdown("---")
    st.markdown("### ✅ Review Your Trip")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Approve Itinerary", use_container_width=True, type="primary"):
            thread_id = st.session_state.thread_id
            config = {"configurable": {"thread_id": thread_id}}
            graph = st.session_state.graph

            save_feedback(thread_id, "approve")

            with st.spinner("Generating final plan..."):
                try:
                    graph.update_state(config, {
                        "human_decision": "approve",
                    })
                    result = graph.invoke(None, config=config)
                    st.session_state.state = result
                    st.session_state.phase = "complete"
                    save_state(thread_id, result)
                    st.rerun()
                except Exception as exc:
                    st.error(f"Error: {exc}")

    with col2:
        if st.button("✏️ Request Changes", use_container_width=True):
            st.session_state.show_feedback = True
            st.rerun()

    # ── Change request form ────────────────────────────────────────
    if st.session_state.get("show_feedback"):
        feedback = st.text_area(
            "What should be changed?",
            placeholder="Make it cheaper and add more cultural activities",
        )
        if st.button("📤 Submit Changes"):
            if feedback.strip():
                thread_id = st.session_state.thread_id
                config = {"configurable": {"thread_id": thread_id}}
                graph = st.session_state.graph

                save_feedback(thread_id, "changes", feedback)

                with st.spinner("Re-planning with your feedback..."):
                    try:
                        graph.update_state(config, {
                            "human_decision": "changes",
                            "human_feedback": feedback,
                        })
                        # This will loop back through supervisor → agents → itinerary
                        for event in graph.stream(None, config=config, stream_mode="updates"):
                            pass

                        snapshot = graph.get_state(config)
                        state = snapshot.values if snapshot else {}
                        st.session_state.state = state
                        st.session_state.show_feedback = False
                        save_state(thread_id, state)
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Error: {exc}")

# ── Phase: Complete ────────────────────────────────────────────────────
elif st.session_state.phase == "complete":
    state = st.session_state.state or {}

    st.success("🎉 Your travel plan is ready!")

    final = state.get("final_response", "")
    if final:
        st.markdown("### 📄 Your Final Travel Plan")
        st.markdown(final)
    else:
        # Fallback: show itinerary directly
        itinerary = state.get("itinerary_plan", "No plan available.")
        st.markdown(itinerary)

    # Budget summary
    budget = state.get("budget_analysis", {})
    if budget:
        st.markdown("### 💰 Budget Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Cost", f"₹{budget.get('estimated_total', 0):,.0f}")
        with col2:
            st.metric("Your Budget", f"₹{budget.get('user_budget', 0):,.0f}")
        with col3:
            st.metric("Status", "✅ Within Budget" if budget.get("within_budget") else "⚠️ Over Budget")

    st.markdown("---")
    st.caption("_All prices are estimated. No bookings have been made. Data sources are labeled accordingly._")

    if st.button("🔄 Plan Another Trip", use_container_width=True):
        st.session_state.phase = "input"
        st.session_state.state = None
        st.session_state.thread_id = None
        st.rerun()
