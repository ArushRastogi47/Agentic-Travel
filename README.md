# ✈️ Agentic Travel Planner

An interactive, local-first travel planning assistant built with LangGraph. Describe a trip in natural language and the application coordinates specialist agents for flights, hotels, weather, budgeting, and itinerary planning.

The project is designed for experimentation and demos: travel data can run entirely from mock providers, while free live adapters are available when demo mode is disabled.

## Features

- **Dynamic orchestration**: a supervisor selects only the specialists needed for each request.
- **Safety guardrails**: off-topic and unsafe requests are blocked before the workflow starts.
- **Parallel research**: flight, hotel, and weather agents can run concurrently.
- **Deterministic budgeting**: cost calculations use Python logic rather than an LLM.
- **Human approval loop**: review a draft itinerary, approve it, or request changes.
- **Persistent sessions**: LangGraph checkpoints and SQLite history allow trips to be resumed.
- **Multiple interfaces**: use the Streamlit UI or the FastAPI REST API.
- **Exports**: download completed itineraries as Markdown or PDF from the UI.
- **Provider abstraction**: switch between mock data and free live adapters without changing the graph.

## Architecture

```text
User request
     │
     ▼
Input guardrail ── blocked ──► End
     │
     ▼
Supervisor
     │
     ├── Flight agent ─┐
     ├── Hotel agent ──┼──► Join specialists
     └── Weather agent ┘          │
                                  ▼
                         Deterministic budget
                                  │
                                  ▼
                           Itinerary agent
                                  │
                                  ▼
                           Human review
                            ┌─────┴─────┐
                         Changes     Approve
                            │           │
                            └──► Supervisor
                                        │
                                  Final response
```

Weather-only and other short requests can skip unnecessary specialists and go directly to a final response.

## Technology

- Python 3.11+
- LangGraph and LangChain
- Google Gemini or Ollama for LLM-powered agents
- Streamlit frontend
- FastAPI and Uvicorn backend
- SQLite with LangGraph SQLite checkpoints
- Open-Meteo, OpenSky Network, and OpenStreetMap adapters
- Pydantic, HTTPX, ReportLab, and pytest

## Requirements

Install:

1. Python 3.11 or newer
2. Git
3. An LLM provider:
   - Google Gemini API key, or
   - [Ollama](https://ollama.com/) with a local model such as `llama3.2`

## Quick start

```bash
git clone <repository-url>
cd travel-agent

python -m venv .venv
source .venv/bin/activate          # macOS/Linux
# .venv\Scripts\activate           # Windows PowerShell

pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and configure an LLM. The default is Gemini:

```dotenv
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
DEMO_MODE=true
```

To use Ollama instead:

```bash
ollama pull llama3.2
ollama serve
```

```dotenv
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

Start the Streamlit application:

```bash
streamlit run app/main.py
```

Open the displayed local URL, enter a travel request, inspect the draft itinerary, and approve it or request changes.

## Configuration

| Variable | Default | Description |
| --- | --- | --- |
| `LLM_PROVIDER` | `gemini` | `gemini` or `ollama` |
| `GEMINI_API_KEY` | empty | API key used when Gemini is selected |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model name |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.2` | Local Ollama model |
| `DEMO_MODE` | `true` | Use deterministic mock travel providers |
| `DATABASE_URL` | `sqlite:///./data/travel_agent.db` | SQLite database location |
| `LOG_LEVEL` | `INFO` | Application log level |
| `OPEN_METEO_BASE_URL` | `https://api.open-meteo.com` | Open-Meteo base URL |

`DEMO_MODE=true` keeps flight, hotel, and weather research offline by using mock adapters. Set it to `false` to enable the free live adapters. Live results may still fall back to estimates when a provider is unavailable.

## FastAPI API

Run the backend:

```bash
uvicorn app.api:app --reload
```

### Create a trip

```bash
curl -X POST http://127.0.0.1:8000/trip \
  -H "Content-Type: application/json" \
  -d '{"query":"Plan a 4-day trip to Goa under ₹20,000"}'
```

The response includes a `thread_id`. Full trip requests pause with `status: "awaiting_review"` after generating a draft.

### Read trip state

```bash
curl http://127.0.0.1:8000/trip/<thread_id>
```

### Approve or request changes

```bash
curl -X POST http://127.0.0.1:8000/trip/<thread_id>/resume \
  -H "Content-Type: application/json" \
  -d '{"decision":"approve","feedback":""}'
```

Use `"decision":"changes"` with feedback such as `"Choose a cheaper hotel"` to send the workflow through another planning iteration.

## Tests

Run the test suite from the project root:

```bash
pytest tests/ -v
```

The tests cover guardrails, supervisor extraction, deterministic budgeting, graph routing, human review, provider tools, and API endpoints.

## Project layout

```text
app/
├── agents/          Specialist and response agents
├── graph/           LangGraph state, nodes, and routing
├── guardrails/      Input validation and safety checks
├── models/          Pydantic data schemas
├── persistence/     SQLite conversation and state storage
├── prompts/         LLM prompt templates
├── tools/           LLM, provider, routing, and export adapters
├── api.py           FastAPI application
├── config.py        Environment configuration
└── main.py          Streamlit application
tests/               Unit and integration tests
data/                Runtime SQLite database files
```

## Data and safety notes

- Mock flight and hotel results are estimates, not live availability.
- Live provider responses are informational and may be incomplete or stale.
- The application does not make bookings or process payments.
- Budget totals are estimates based on the inputs and available provider data.
- Keep API keys in `.env`; do not commit secrets.
