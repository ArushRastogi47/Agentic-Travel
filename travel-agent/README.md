# ✈️ LangGraph Agentic Travel Planner

A **free-to-run, local-first agentic AI travel planner** built with **LangGraph**, **Ollama**, and **Streamlit**.

> ⚠️ Zero-cost: No paid APIs, no cloud services, runs entirely on your machine.

## Architecture

```
USER → [Input Guardrail] → [Supervisor Agent]
                              ↓ dynamic selection
         ┌──────────────┬──────────────┬──────────────┐
    [Flight Agent]  [Hotel Agent]  [Weather Agent]
         └──────────────┴──────────────┘
                        ↓
                 [Budget Agent]     (deterministic)
                        ↓
                [Itinerary Agent]   (LLM-powered)
                        ↓
                 [Human Review]     ← approve / request changes
                        ↓
                [Final Response]
                        ↓
               [Persistence / DB]
```

### Key Design Decisions
- **Supervisor dynamically selects** which agents to run (not hard-coded)
- **Budget calculations are deterministic** (no LLM for arithmetic)
- **Every data source is behind an adapter** (swap live ↔ mock)
- **Human-in-the-loop** with approve/change-request cycle
- **All data is labeled** with provenance (live / estimated / mock)

## Tech Stack

| Component | Choice | Cost |
|-----------|--------|------|
| Language | Python 3.11+ | Free |
| Orchestration | LangGraph | Free |
| LLM | Ollama (local) | Free |
| Backend | FastAPI | Free |
| Frontend | Streamlit | Free |
| Database | SQLite | Free |
| Weather | Open-Meteo | Free |
| Flights/Hotels | Mock adapters | Free |

## Quick Start

### Prerequisites
1. **Python 3.11+** installed
2. **Ollama** installed ([ollama.ai](https://ollama.ai))
3. **Git** installed

### Setup

```bash
# 1. Clone / enter directory
cd travel-agent

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Pull a local model (requires Ollama running)
ollama pull llama3.2

# 5. Configure (optional — defaults work in demo mode)
cp .env.example .env
# Edit .env if needed

# 6. Run the app
streamlit run app/main.py
```

### Run with FastAPI (optional)

```bash
uvicorn app.api:app --reload
```

API endpoints:
- `POST /trip` — Start a new trip
- `POST /trip/{id}/resume` — Submit human feedback
- `GET /trip/{id}` — Get trip state

## Demo Mode

Set `DEMO_MODE=true` in `.env` (default). This uses mock data providers — **no external APIs or Ollama needed for the UI to function** (though Ollama is needed for LLM-powered agents like Supervisor and Itinerary).

## Project Structure

```
travel-agent/
├── app/
│   ├── main.py              # Streamlit UI
│   ├── api.py               # FastAPI backend
│   ├── config.py            # Configuration
│   ├── logging_config.py    # Logging setup
│   ├── graph/
│   │   ├── state.py         # TravelState (shared state)
│   │   ├── graph.py         # LangGraph graph builder
│   │   ├── nodes.py         # Node wrappers
│   │   └── routing.py       # Conditional routing
│   ├── agents/
│   │   ├── supervisor.py    # Supervisor (LLM)
│   │   ├── flight_agent.py  # Flight search
│   │   ├── hotel_agent.py   # Hotel search
│   │   ├── weather_agent.py # Weather data
│   │   ├── budget_agent.py  # Budget calc (deterministic)
│   │   ├── itinerary_agent.py   # Itinerary (LLM)
│   │   └── final_response_agent.py  # Final output (LLM)
│   ├── guardrails/
│   │   └── input_guardrail.py   # Input validation
│   ├── tools/
│   │   ├── llm.py           # Ollama wrapper
│   │   ├── weather.py       # Weather providers
│   │   ├── flights.py       # Flight providers
│   │   ├── hotels.py        # Hotel providers
│   │   ├── places.py        # Places/attractions
│   │   └── routing.py       # Transport estimation
│   ├── models/
│   │   └── schemas.py       # Pydantic models
│   ├── persistence/
│   │   └── database.py      # SQLite persistence
│   └── prompts/
│       ├── supervisor.txt
│       ├── itinerary.txt
│       └── final_response.txt
├── tests/
│   ├── test_guardrail.py
│   ├── test_supervisor.py
│   ├── test_budget.py
│   ├── test_graph.py
│   └── test_human_loop.py
├── data/                    # SQLite database (auto-created)
├── requirements.txt
├── .env.example
└── .env
```

## Running Tests

```bash
pytest tests/ -v
```

## Concepts Demonstrated

- ✅ LangGraph stateful agents
- ✅ Supervisor architecture with dynamic routing
- ✅ Conditional edges & parallel execution
- ✅ Specialist agents (flight, hotel, weather, budget, itinerary)
- ✅ Tool calling with provider abstraction
- ✅ Structured outputs (Pydantic models)
- ✅ Human-in-the-loop (approve / change cycle)
- ✅ Deterministic + LLM hybrid architecture
- ✅ Persistence & checkpointing (SQLite + LangGraph MemorySaver)
- ✅ Error handling & graceful degradation
- ✅ Data provenance (live / estimated / mock labels)
- ✅ Offline demo mode
- ✅ Unit & integration tests

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `Connection refused` on LLM calls | Make sure Ollama is running: `ollama serve` |
| Model not found | Run `ollama pull llama3.2` |
| Import errors | Ensure venv is activated and `pip install -r requirements.txt` was run |
| Streamlit not loading | Check Python version ≥ 3.11 |

## Important Disclaimers

- All flight and hotel data in demo mode is **estimated/mock** — not real availability
- No bookings are made — this is a planning tool only
- Weather data from Open-Meteo is live when `DEMO_MODE=false`
- Budget calculations are estimates based on average costs
