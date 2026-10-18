"""
Streamlit UI for the LangGraph Travel Agent.

Features:
- Natural language travel planning input with quick examples
- Real-time agent streaming status tracking
- Dynamic specialist display with Mock vs Live data tags
- Human-in-the-loop approval & change request cycle
- Recent trips sidebar history with 1-click reload
- PDF and Markdown itinerary exports
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

# Add project root to path for imports
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import streamlit as st

import importlib
import os
import app.config
importlib.reload(app.config)

DEMO_MODE = getattr(app.config, "DEMO_MODE", True)
LLM_PROVIDER = getattr(app.config, "LLM_PROVIDER", os.getenv("LLM_PROVIDER", "gemini"))
GEMINI_API_KEY = getattr(app.config, "GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
GEMINI_MODEL = getattr(app.config, "GEMINI_MODEL", os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
OLLAMA_MODEL = getattr(app.config, "OLLAMA_MODEL", os.getenv("OLLAMA_MODEL", "llama3.2"))

from app.graph.graph import build_graph

from app.logging_config import logger
from app.persistence.database import (
    get_latest_state,
    get_recent_conversations,
    init_database,
    save_conversation,
    save_feedback,
    save_state,
)
from app.tools.export import generate_markdown, generate_pdf

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
        background: linear-gradient(120deg, #4f46e5 0%, #7c3aed 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 0.5rem 0 0.2rem 0;
    }
    .status-item {
        padding: 0.35rem 0.5rem;
        font-size: 0.95rem;
        border-radius: 6px;
        background: rgba(255, 255, 255, 0.05);
        margin-bottom: 0.3rem;
    }
    .badge-mock {
        background-color: #f59e0b;
        color: #000;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-live {
        background-color: #10b981;
        color: #fff;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# ── Initialization ─────────────────────────────────────────────────────

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
    if "show_feedback" not in st.session_state:
        st.session_state.show_feedback = False
    if "trip_query" not in st.session_state:
        st.session_state.trip_query = ""


init()


# ── Sidebar ────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚙️ Control Panel")
    st.caption("Local-first • Zero-Cost Architecture")

    # Determine active key
    active_key = os.getenv("GEMINI_API_KEY", "") or GEMINI_API_KEY
    is_gemini = (LLM_PROVIDER == "gemini")

    if is_gemini:
        st.markdown(f"**LLM:** 🌟 `Google Gemini`")
        st.markdown(f"**Model:** `{GEMINI_MODEL}`")
        if active_key:
            st.success("🔑 Gemini API Key: Active")
        else:
            st.warning("⚠️ Gemini API Key: Missing in `.env`")
            user_key_input = st.text_input("Enter Gemini API Key:", type="password", key="sidebar_gemini_key")
            if user_key_input:
                os.environ["GEMINI_API_KEY"] = user_key_input
                st.success("Key applied for this session!")
                st.rerun()
    else:
        st.info(f"**LLM:** `Ollama`\n\n**Model:** `{OLLAMA_MODEL}`")

    st.markdown(f"**Mode:** {'🟡 Mock / Demo' if DEMO_MODE else '🟢 Live APIs'}")

    if st.button("➕ New Trip Plan", use_container_width=True, type="primary"):
        st.session_state.thread_id = None
        st.session_state.state = None
        st.session_state.phase = "input"
        st.session_state.show_feedback = False
        st.session_state.trip_query = ""
        st.rerun()


    st.markdown("---")
    st.markdown("### 📊 Active Workflow Status")
    if st.session_state.state:
        statuses = st.session_state.state.get("workflow_status", [])
        if statuses:
            for s in statuses:
                st.markdown(f"<div class='status-item'>{s}</div>", unsafe_allow_html=True)
        else:
            st.markdown("_Workflow running..._")
    else:
        st.markdown("_No active trip session_")

    st.markdown("---")
    st.markdown("### 🗂️ Recent Trips")
    try:
        recents = get_recent_conversations(limit=6)
        if recents:
            for rec in recents:
                tid = rec["id"]
                query_preview = (rec["user_query"][:32] + "...") if len(rec["user_query"]) > 32 else rec["user_query"]
                if st.button(f"📍 {query_preview}", key=f"hist_{tid}", use_container_width=True):
                    loaded_state = get_latest_state(tid)
                    if loaded_state:
                        st.session_state.thread_id = tid
                        st.session_state.state = loaded_state
                        if loaded_state.get("final_response"):
                            st.session_state.phase = "complete"
                        elif loaded_state.get("itinerary_plan"):
                            st.session_state.phase = "review"
                        else:
                            st.session_state.phase = "complete"
                        st.rerun()
        else:
            st.caption("No previous trips saved yet.")
    except Exception as exc:
        logger.error(f"[Sidebar] Could not load recents: {exc}")

    st.markdown("---")
    st.caption("Built with LangGraph, Ollama, OpenMeteo & SQLite")


# ── Main Header ────────────────────────────────────────────────────────

st.markdown("<h1 class='main-header'>✈️ Autonomous Travel Agent</h1>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align: center; color: #9ca3af; margin-bottom: 2rem;'>"
    "Dynamic multi-agent planner with deterministic budgeting, human approval, and zero-cost local execution"
    "</p>",
    unsafe_allow_html=True,
)


# ── Friendly streaming node mapper ─────────────────────────────────────

FRIENDLY_NODE_LABELS = {
    "guardrail": "🛡️ Validating trip request against safety guidelines...",
    "supervisor": "🧭 Supervisor analyzing intent and activating specialist agents...",
    "flight_agent": "✈️ Flight Agent researching routes and pricing...",
    "hotel_agent": "🏨 Hotel Agent finding accommodations and ratings...",
    "weather_agent": "🌤️ Weather Agent fetching meteorological forecasts...",
    "join_specialists": "🔄 Merging specialist research findings...",
    "budget_agent": "💰 Budget Agent calculating deterministic cost estimates...",
    "itinerary_agent": "📅 Itinerary Agent drafting personalized daily schedule...",
    "final_response": "✨ Final Response Agent formatting comprehensive plan...",
}


# ── Phase: Input ───────────────────────────────────────────────────────

if st.session_state.phase == "input":
    st.markdown("### 🌍 Where would you like to go?")

    # Example query pills
    st.caption("💡 Click an example to load:")
    col_e1, col_e2, col_e3 = st.columns(3)
    if col_e1.button("🏖️ 4-day Goa beach under ₹20,000", use_container_width=True):
        st.session_state.trip_query = "Plan a 4-day trip to Goa under ₹20,000"
        st.rerun()
    if col_e2.button("🏙️ 5-day Dubai trip under ₹80,000", use_container_width=True):
        st.session_state.trip_query = "Plan a 5-day trip to Dubai next month under ₹80,000"
        st.rerun()
    if col_e3.button("🌤️ Weather forecast for Paris", use_container_width=True):
        st.session_state.trip_query = "What is the weather in Paris next week?"
        st.rerun()

    with st.form("plan_trip_form", clear_on_submit=False):
        query = st.text_area(
            "Describe your trip",
            value=st.session_state.get("trip_query", ""),
            placeholder="e.g. Plan a 4-day trip to Dubai next month under ₹80,000 with flights from Delhi",
            height=100,
            label_visibility="collapsed",
        )

        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            plan_btn = st.form_submit_button("🚀 Plan My Trip", use_container_width=True, type="primary")

    if plan_btn:
        clean_query = query.strip()
        if not clean_query:
            st.warning("⚠️ Please enter a travel destination or request, or click one of the examples above!")
        else:
            st.session_state.trip_query = clean_query
            thread_id = str(uuid.uuid4())[:8]
            st.session_state.thread_id = thread_id
            save_conversation(thread_id, clean_query)

            config = {"configurable": {"thread_id": thread_id}}
            initial_state = {"user_query": clean_query, "iteration": 0}

            status_box = st.status("🚀 Agentic workflow starting...", expanded=True)
            try:
                graph = st.session_state.graph
                for event in graph.stream(initial_state, config=config, stream_mode="updates"):
                    for node_name, _ in event.items():
                        if node_name == "__interrupt__":
                            continue
                        label = FRIENDLY_NODE_LABELS.get(node_name, f"Executing {node_name}...")
                        status_box.write(label)

                snapshot = graph.get_state(config)
                state = snapshot.values if snapshot else {}
                st.session_state.state = state

                status_box.update(label="✅ Workflow processing completed!", state="complete", expanded=False)

                if state.get("validation_status") == "block":
                    st.session_state.phase = "blocked"
                elif state.get("final_response"):
                    # Direct route (e.g. weather-only, budget-only)
                    st.session_state.phase = "complete"
                else:
                    st.session_state.phase = "review"

                save_state(thread_id, state)
                st.rerun()

            except Exception as exc:
                status_box.update(label="❌ Error occurred", state="error")
                st.error(f"Execution Error: {exc}")
                logger.error(f"[UI] Graph execution failed: {exc}", exc_info=True)


# ── Phase: Blocked ─────────────────────────────────────────────────────

elif st.session_state.phase == "blocked":
    state = st.session_state.state or {}
    st.error("❌ **Request Blocked by Guardrail**")
    st.warning(f"Reason: {state.get('validation_reason', 'Prompt violates safe travel policy.')}")
    st.info("The travel planner only assists with legitimate travel, destination research, itineraries, flights, and hotels.")

    if st.button("↩️ Try Another Request", type="primary"):
        st.session_state.phase = "input"
        st.session_state.state = None
        st.session_state.trip_query = ""
        st.rerun()


# ── Phase: Review (Human-in-the-Loop) ───────────────────────────────────

elif st.session_state.phase == "review":
    state = st.session_state.state or {}
    constraints = state.get("trip_constraints", {})
    dest = constraints.get("destination", "Your Destination")
    duration = constraints.get("duration_days", 4)

    st.markdown(f"## 📋 Draft Plan for {dest} ({duration} Days)")

    # ── Budget Highlights ──────────────────────────────────────────
    budget = state.get("budget_analysis", {})
    if budget:
        st.markdown("### 💰 Deterministic Budget Analysis")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Estimated Cost", f"₹{budget.get('estimated_total', 0):,.0f}")
        with col2:
            st.metric("Your Budget", f"₹{budget.get('user_budget', 0):,.0f}")
        with col3:
            rem = budget.get("remaining_budget", 0)
            st.metric(
                "Variance",
                f"₹{rem:,.0f}",
                delta="Within Budget" if budget.get("within_budget") else "Over Budget",
            )
        with col4:
            st.metric("Budget Health", "✅ Approved" if budget.get("within_budget") else "⚠️ Over Limit")

    st.markdown("---")

    # ── Tabs for specialist details ────────────────────────────────
    tab_itin, tab_flights, tab_hotels, tab_weather = st.tabs(
        ["📅 Detailed Itinerary", "✈️ Flight Options", "🏨 Accommodations", "🌤️ Weather Forecast"]
    )

    with tab_itin:
        itinerary = state.get("itinerary_plan", "No itinerary plan generated.")
        st.markdown(itinerary)

    with tab_flights:
        flights = state.get("flight_results", [])
        if flights:
            for i, f in enumerate(flights, 1):
                badge_type = f.get("data_type", "mock")
                badge_html = (
                    "<span class='badge-live'>LIVE</span>"
                    if badge_type == "live"
                    else "<span class='badge-mock'>MOCK</span>"
                )
                with st.expander(
                    f"Option {i}: {f.get('airline', 'Airline')} — ₹{f.get('price', 0):,.0f} ({f.get('currency', 'INR')})",
                    expanded=(i == 1),
                ):
                    st.markdown(f"**Data Source:** {badge_html} `{f.get('source', 'Provider')}`", unsafe_allow_html=True)
                    st.write(f"**Route:** {f.get('origin', 'DEL')} → {f.get('destination', dest)}")
                    st.write(f"**Departure:** `{f.get('departure', 'N/A')}` | **Arrival:** `{f.get('arrival', 'N/A')}`")
                    st.write(f"**Flight Duration:** {f.get('duration_minutes', 0)} mins")
        else:
            st.info("No flight research requested or available.")

    with tab_hotels:
        hotels = state.get("hotel_results", [])
        if hotels:
            for i, h in enumerate(hotels, 1):
                badge_type = h.get("data_type", "mock")
                badge_html = (
                    "<span class='badge-live'>LIVE</span>"
                    if badge_type == "live"
                    else "<span class='badge-mock'>MOCK</span>"
                )
                with st.expander(
                    f"Option {i}: {h.get('name', 'Hotel')} — ₹{h.get('nightly_price', 0):,.0f} / night",
                    expanded=(i == 1),
                ):
                    st.markdown(f"**Data Source:** {badge_html} `{h.get('source', 'Provider')}`", unsafe_allow_html=True)
                    st.write(f"**Rating:** ★ {h.get('rating', '4.0')} / 5.0")
                    st.write(f"**Total Stay Price:** ₹{h.get('total_price', 0):,.0f}")
                    if h.get("amenities"):
                        st.write(f"**Amenities:** {', '.join(h['amenities'])}")
        else:
            st.info("No hotel research requested or available.")

    with tab_weather:
        weather = state.get("weather_info", {})
        if weather and weather.get("daily"):
            badge_type = weather.get("data_type", "live")
            badge_html = (
                "<span class='badge-live'>LIVE API</span>"
                if badge_type == "live"
                else "<span class='badge-mock'>MOCK</span>"
            )
            st.markdown(f"**Provider:** {badge_html} `{weather.get('source', 'Open-Meteo')}`", unsafe_allow_html=True)
            cols = st.columns(min(len(weather["daily"]), 6))
            for i, day in enumerate(weather["daily"][:6]):
                with cols[i]:
                    st.markdown(f"**{day.get('date', '')}**")
                    st.markdown(f"**{day.get('description', '')}**")
                    st.markdown(f"🌡️ High: `{day.get('temperature_high')}°C`")
                    st.markdown(f"❄️ Low: `{day.get('temperature_low')}°C`")
                    st.markdown(f"🌧️ Rain: `{day.get('rain_probability')}%`")

            if weather.get("packing_suggestions"):
                st.markdown("#### 🎒 Packing Suggestions")
                for pack in weather["packing_suggestions"]:
                    st.markdown(f"- {pack}")
        else:
            st.info("Weather forecast not available.")

    # ── Human Decision Controls ────────────────────────────────────
    st.markdown("---")
    st.markdown("### 👤 Human Review & Decision")
    st.write("Review the proposed plan above. You can approve it to generate the final itinerary, or request specific modifications.")

    iter_count = state.get("iteration", 1)
    if iter_count > 1:
        st.info(f"🔄 Re-plan iteration: **{iter_count} of 3**")

    col_app, col_mod = st.columns(2)
    with col_app:
        if st.button("✅ Approve Itinerary", use_container_width=True, type="primary"):
            thread_id = st.session_state.thread_id
            config = {"configurable": {"thread_id": thread_id}}
            graph = st.session_state.graph

            save_feedback(thread_id, "approve")
            with st.spinner("✨ Synthesizing final travel package..."):
                try:
                    graph.update_state(config, {"human_decision": "approve"})
                    result = graph.invoke(None, config=config)
                    st.session_state.state = result
                    st.session_state.phase = "complete"
                    save_state(thread_id, result)
                    st.rerun()
                except Exception as exc:
                    st.error(f"Approval failed: {exc}")

    with col_mod:
        if st.button("✏️ Request Modifications", use_container_width=True):
            st.session_state.show_feedback = not st.session_state.show_feedback
            st.rerun()

    if st.session_state.get("show_feedback"):
        st.markdown("#### 💬 Provide Change Instructions")
        change_input = st.text_area(
            "What would you like to adjust?",
            placeholder="e.g. Find cheaper hotels, add more water sports in Goa, or adjust for a tighter budget",
            key="feedback_text",
        )
        if st.button("🚀 Re-plan with Changes", type="primary"):
            if change_input.strip():
                thread_id = st.session_state.thread_id
                config = {"configurable": {"thread_id": thread_id}}
                graph = st.session_state.graph

                save_feedback(thread_id, "changes", change_input)

                status_box = st.status("🔄 Re-evaluating plan with your feedback...", expanded=True)
                try:
                    graph.update_state(
                        config,
                        {
                            "human_decision": "changes",
                            "human_feedback": change_input,
                        },
                    )
                    for event in graph.stream(None, config=config, stream_mode="updates"):
                        for node_name, _ in event.items():
                            if node_name == "__interrupt__":
                                continue
                            label = FRIENDLY_NODE_LABELS.get(node_name, f"Executing {node_name}...")
                            status_box.write(label)

                    snapshot = graph.get_state(config)
                    new_state = snapshot.values if snapshot else {}
                    st.session_state.state = new_state
                    st.session_state.show_feedback = False
                    status_box.update(label="✅ Changes successfully applied!", state="complete", expanded=False)
                    save_state(thread_id, new_state)
                    st.rerun()
                except Exception as exc:
                    status_box.update(label="❌ Re-plan error", state="error")
                    st.error(f"Re-planning error: {exc}")


# ── Phase: Complete ────────────────────────────────────────────────────

elif st.session_state.phase == "complete":
    state = st.session_state.state or {}
    constraints = state.get("trip_constraints", {})
    dest = constraints.get("destination", "Trip")

    st.success("🎉 **Your Travel Plan is Complete & Confirmed!**")

    final_content = state.get("final_response") or state.get("itinerary_plan", "No plan available.")
    st.markdown(final_content)

    # ── Export Controls ────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 💾 Export Your Itinerary")

    col_exp1, col_exp2, col_exp3 = st.columns([1, 1, 1])

    with col_exp1:
        md_text = generate_markdown(state)
        st.download_button(
            label="📥 Download Markdown (.md)",
            data=md_text,
            file_name=f"itinerary_{dest.lower().replace(' ', '_')}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with col_exp2:
        try:
            pdf_bytes = generate_pdf(state)
            st.download_button(
                label="📄 Download PDF (.pdf)",
                data=pdf_bytes,
                file_name=f"itinerary_{dest.lower().replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary",
            )
        except Exception as exc:
            st.caption(f"PDF generation error: {exc}")

    with col_exp3:
        if st.button("🔄 Plan Another Trip", use_container_width=True):
            st.session_state.phase = "input"
            st.session_state.state = None
            st.session_state.thread_id = None
            st.session_state.show_feedback = False
            st.session_state.trip_query = ""
            st.rerun()

    st.markdown("---")
    st.caption("All estimates are calculated locally. No actual bookings or financial transactions have been conducted.")
