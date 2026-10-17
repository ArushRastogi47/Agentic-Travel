# LangGraph Agentic Travel Planner --- Zero-Cost Project Specification

## 1. Purpose

Build a **free-to-run, local-first agentic AI travel planner** using
**LangGraph**.

The system accepts a natural-language travel request such as:

> "Plan a 4 day trip to Dubai for next month."

It should:

1.  Validate the request.
2.  Understand the user's intent and constraints.
3.  Dynamically decide which specialist agents are actually needed.
4.  Run those agents through a shared LangGraph state.
5.  Let the user review the generated itinerary.
6.  Allow the user to request changes and loop back to relevant agents.
7.  Generate a final structured travel plan.
8.  Persist conversation/state/checkpoints locally.

The architecture is based on the supplied diagram.

------------------------------------------------------------------------

# 2. Critical Zero-Cost Requirement

## Non-negotiable constraint

The project must be runnable without paying for:

-   OpenAI API
-   Anthropic API
-   Tavily paid API
-   AviationStack paid API
-   paid hotel APIs
-   paid hosting
-   paid database hosting
-   paid vector databases

Use local/open/free components wherever possible.

### Recommended stack

  ----------------------------------------------------------------------------
  Component             Choice                                            Cost
  --------------------- ------------------------- ----------------------------
  Language              Python 3.11+                                      Free

  Agent orchestration   LangGraph                             Free/open source

  LLM                   Ollama + local model                              Free

  LLM model             Llama 3.x / Qwen /                                Free
                        another compatible local  
                        model                     

  Web/backend           FastAPI                                           Free

  Frontend              Streamlit initially                               Free

  Database              SQLite for simplest                               Free
                        version                   

  Optional DB           PostgreSQL locally                                Free

  Weather               Open-Meteo                  Free/no API key for normal
                                                                           use

  Maps/routing          OSRM or                                      Free/open
                        OpenStreetMap-based       
                        services                  

  Places                OpenStreetMap / Overpass       Free subject to service
                                                                        limits

  Flight data           OpenSky Network or a mock        Free with limitations
                        adapter                   

  Hotel data            OpenStreetMap/Geocoding          Free with limitations
                        or mock adapter           

  Version control       Git                                               Free
  ----------------------------------------------------------------------------

## Important limitation

A truly zero-cost project cannot guarantee live commercial booking
inventory, guaranteed flight fares, hotel availability, or ticket
purchases.

The application should clearly label external information as:

-   live/queried data,
-   estimated data,
-   cached data,
-   or demo/mock data.

Do **not** pretend that mock results are real bookings.

------------------------------------------------------------------------

# 3. Architecture

Implement this logical flow:

``` text
USER
  |
  v
[INPUT GUARDRAIL]
  |
  +---- BLOCK ----> Explain reason and stop
  |
  v
[SUPERVISOR AGENT]
  |
  | dynamically selects specialists
  v
+-------------------+------------------+------------------+
| Flight Agent      | Hotel Agent      | Weather Agent    |
|                   |                  |                  |
| flight data       | hotel data       | forecast/climate |
+-------------------+------------------+------------------+
          +----------------+----------------+
          | Budget Agent   | Itinerary Agent|
          +----------------+----------------+
                   |
                   v
             [SHARED STATE]
                   |
                   v
          [HUMAN-IN-THE-LOOP]
             /           \
        APPROVE         CHANGES
           |               |
           |               +----> Supervisor / relevant agents
           v
      [FINAL RESPONSE]
           |
           v
 [PERSISTENCE / CHECKPOINT]
```

------------------------------------------------------------------------

# 4. Important Architecture Improvement

Do not make every specialist call the LLM.

Use the LLM where reasoning is actually needed.

Recommended division:

### LLM-heavy components

-   Input interpretation
-   Supervisor
-   Itinerary reasoning
-   Final response generation

### Mostly deterministic components

-   Budget calculations
-   Date calculations
-   Currency arithmetic
-   Travel-duration calculations
-   Validation
-   State merging
-   Result ranking
-   Constraint checks

### External-data components

-   Flight search
-   Hotel/places search
-   Weather lookup
-   Routing

This makes the system cheaper, faster, easier to debug, and more
reliable.

------------------------------------------------------------------------

# 5. Suggested Project Structure

Create this structure:

``` text
travel-agent/
│
├── README.md
├── .env.example
├── .gitignore
├── requirements.txt
│
├── app/
│   ├── __init__.py
│   │
│   ├── main.py
│   │
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── state.py
│   │   ├── graph.py
│   │   ├── nodes.py
│   │   └── routing.py
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── supervisor.py
│   │   ├── flight_agent.py
│   │   ├── hotel_agent.py
│   │   ├── weather_agent.py
│   │   ├── budget_agent.py
│   │   ├── itinerary_agent.py
│   │   └── final_response_agent.py
│   │
│   ├── guardrails/
│   │   ├── __init__.py
│   │   └── input_guardrail.py
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── llm.py
│   │   ├── weather.py
│   │   ├── flights.py
│   │   ├── hotels.py
│   │   ├── places.py
│   │   └── routing.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py
│   │
│   ├── persistence/
│   │   ├── __init__.py
│   │   └── database.py
│   │
│   └── prompts/
│       ├── supervisor.txt
│       ├── itinerary.txt
│       └── final_response.txt
│
├── tests/
│   ├── test_guardrail.py
│   ├── test_supervisor.py
│   ├── test_budget.py
│   ├── test_graph.py
│   └── test_human_loop.py
│
└── data/
    └── travel_agent.db
```

------------------------------------------------------------------------

# 6. Core State

Create a strongly typed shared state.

Use a `TypedDict` or equivalent LangGraph state definition.

Suggested state:

``` python
class TravelState(TypedDict, total=False):
    user_query: str

    trip_constraints: dict

    selected_agents: list[str]
    supervisor_reasoning: str

    flight_results: list[dict]
    hotel_results: list[dict]
    weather_info: dict
    budget_analysis: dict
    itinerary_plan: dict

    messages: list
    llm_calls: list

    human_feedback: str
    human_decision: str

    validation_status: str
    validation_reason: str

    final_response: str

    iteration: int
```

Do not store unnecessary duplicate information.

The state is the shared contract between agents.

------------------------------------------------------------------------

# 7. Input Guardrail

The first node must validate the request.

Check:

-   Is this actually a travel-planning request?
-   Is the destination understandable?
-   Is the request sufficiently specified?
-   Is it safe?
-   Does it violate application policy?
-   Is the requested date logically valid?

Example:

``` text
User:
"Plan a 4 day trip to Dubai for next month."

Result:
PASS

User:
"Help me hack an airline booking system."

Result:
BLOCK
Reason:
The request is outside the supported travel-planning scope.
```

The guardrail should return structured output:

``` python
{
    "allowed": True,
    "reason": "...",
    "normalized_request": "..."
}
```

If blocked, the graph must terminate cleanly.

------------------------------------------------------------------------

# 8. Supervisor Agent

The supervisor is the most important new component in the architecture.

Its job is NOT to perform the actual travel research.

Its job is to decide:

1.  What the user wants.
2.  Which constraints matter.
3.  Which specialist agents are needed.
4.  In what logical order they should execute.
5.  Why those agents are required.

Example:

``` text
User:
"Plan a 4-day Dubai trip next month under ₹80,000."

Supervisor:

selected_agents:
- flight
- hotel
- weather
- budget
- itinerary
```

Another example:

``` text
User:
"What will the weather in Dubai be like next weekend?"

Supervisor:

selected_agents:
- weather

No need to call flight/hotel/budget agents.
```

Use structured output rather than parsing free-form text.

Example:

``` json
{
  "selected_agents": [
    "flight",
    "hotel",
    "weather",
    "budget",
    "itinerary"
  ],
  "trip_constraints": {
    "destination": "Dubai",
    "duration_days": 4,
    "budget_inr": 80000
  },
  "reasoning": "Flight and hotel are needed for cost estimation..."
}
```

Do not expose private chain-of-thought to the user.

Store only a short operational reason such as:

> "Budget agent selected because the user specified a total trip
> budget."

------------------------------------------------------------------------

# 9. Specialist Agents

## 9.1 Flight Agent

Responsibilities:

-   Search available flight information.
-   Compare routes.
-   Compare departure/arrival times.
-   Estimate fares.
-   Return normalized results.

Interface:

``` python
def search_flights(state: TravelState) -> dict:
    ...
```

Use an adapter architecture:

``` text
FlightAgent
    |
    +-- OpenSkyAdapter
    |
    +-- MockFlightAdapter
```

The graph should not depend directly on one provider.

If live flight pricing is unavailable, return demo/estimated data and
clearly mark it.

------------------------------------------------------------------------

# 10. Hotel Agent

Responsibilities:

-   Find accommodation candidates.
-   Compare estimated prices.
-   Compare location.
-   Compare amenities.
-   Return normalized results.

Use:

``` text
HotelAgent
    |
    +-- OpenStreetMapAdapter
    |
    +-- MockHotelAdapter
```

Do not claim that a hotel is actually available for booking unless the
source explicitly confirms availability.

------------------------------------------------------------------------

# 11. Weather Agent

Prefer Open-Meteo for the free version.

Responsibilities:

-   Forecast when available.
-   Historical climate information when appropriate.
-   Temperature.
-   Rain probability.
-   Weather-related packing suggestions.

This agent can be mostly deterministic after obtaining the API data.

------------------------------------------------------------------------

# 12. Budget Agent

The budget agent should preferably be deterministic.

Inputs:

``` text
flight cost
hotel cost
transport estimate
food estimate
activities estimate
miscellaneous buffer
```

Example:

``` python
total =
    flights +
    hotels +
    transport +
    food +
    activities +
    miscellaneous
```

Then compare:

``` text
estimated_total <= user_budget
```

Return:

``` json
{
  "estimated_total": 73500,
  "user_budget": 80000,
  "remaining_budget": 6500,
  "within_budget": true
}
```

Do not ask an LLM to perform arithmetic when normal Python can do it.

------------------------------------------------------------------------

# 13. Itinerary Agent

Responsibilities:

-   Convert research results into a day-by-day itinerary.
-   Respect trip duration.
-   Respect budget.
-   Avoid impossible travel sequences.
-   Group geographically close activities.
-   Consider weather.
-   Include transport assumptions.
-   Include approximate time blocks.

Example:

``` text
Day 1
09:00 Arrival
11:00 Hotel check-in
13:00 Lunch
15:00 Burj Khalifa
18:00 Dubai Mall
20:00 Dinner

Day 2
...
```

The itinerary agent can use the local LLM for planning/reasoning.

------------------------------------------------------------------------

# 14. Human-in-the-Loop

This is essential.

Do not immediately produce the final response.

After generating the itinerary:

``` text
Generate itinerary
       |
       v
Human review
       |
   +---+---+
   |       |
Approve   Changes
   |       |
   |       v
   |   Identify affected agents
   |       |
   |       v
   |   Re-run relevant agents
   |       |
   +-------+
       |
       v
Final response
```

Example:

``` text
User:
"Looks good, but make the trip cheaper."

System:
- Update budget constraint.
- Re-run budget agent.
- Potentially re-run hotel agent.
- Re-run itinerary agent.
- Ask for approval again.
```

Do NOT rerun every agent unnecessarily.

------------------------------------------------------------------------

# 15. LangGraph Design

Use conditional routing.

Conceptually:

``` python
START
  -> guardrail
  -> supervisor
  -> dynamic specialist routing
  -> itinerary
  -> human_review
      -> approve -> final_response
      -> changes -> supervisor/relevant_agents
  -> persistence
  -> END
```

The supervisor should dynamically determine which nodes need execution.

Do not create a hard-coded workflow like:

``` text
flight -> hotel -> weather -> budget -> itinerary
```

for every request.

Instead:

``` text
supervisor
    |
    +--> selected specialists
```

------------------------------------------------------------------------

# 16. Parallel Execution

Where possible, independent agents should run in parallel.

For example:

``` text
Supervisor
    |
    +---- Flight
    |
    +---- Hotel
    |
    +---- Weather
```

Then:

``` text
Flight
   \
Hotel ----> Budget ----> Itinerary
   /
Weather
```

Do not force weather to wait for hotel results if it does not depend on
them.

------------------------------------------------------------------------

# 17. Persistence

For the first version, use SQLite.

Store:

-   conversation/session ID
-   user query
-   state/checkpoints
-   human feedback
-   final itinerary
-   timestamps

LangGraph checkpointing should be used where appropriate.

PostgreSQL can be added later.

Do not start with a remote database.

------------------------------------------------------------------------

# 18. Local LLM

Use Ollama.

Install Ollama locally and run a model supported by the user's machine.

Example models can include:

``` text
llama3.x
qwen
gemma
```

The exact model should be configurable.

Example environment variable:

``` env
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
```

Do not hard-code the model name throughout the project.

------------------------------------------------------------------------

# 19. Tool Abstraction

Every external data source must be behind an adapter.

For example:

``` python
class WeatherProvider(Protocol):
    def get_weather(
        self,
        location: str,
        start_date: str,
        end_date: str
    ) -> dict:
        ...
```

Then:

``` text
WeatherProvider
    |
    +-- OpenMeteoWeatherProvider
    +-- MockWeatherProvider
```

This makes testing possible without internet access.

Do the same for:

-   flights
-   hotels
-   places
-   routing

------------------------------------------------------------------------

# 20. Offline Demo Mode

The application MUST have an offline demo mode.

Example:

``` env
DEMO_MODE=true
```

When enabled:

-   no external API is required,
-   sample flight results are returned,
-   sample hotel results are returned,
-   sample weather results are returned,
-   the complete LangGraph workflow still executes.

This is important for demonstrations and testing.

------------------------------------------------------------------------

# 21. UI

Start with Streamlit.

The UI should contain:

### Input

``` text
Where do you want to travel?

[ Plan a 4 day trip to Dubai next month ]
```

### Workflow status

``` text
✓ Request validated
✓ Supervisor selected agents
✓ Flight research complete
✓ Hotel research complete
✓ Weather research complete
✓ Budget calculated
✓ Itinerary generated
```

### Itinerary

Display the generated plan.

### Human approval

Buttons:

``` text
[ Approve itinerary ]
[ Request changes ]
```

If changes are requested:

``` text
What should be changed?

[ Make it cheaper and add more cultural activities ]
```

Then resume the graph.

------------------------------------------------------------------------

# 22. API Design

If FastAPI is used, expose a simple API.

Suggested endpoints:

``` text
POST /trip
POST /trip/{thread_id}/resume
GET  /trip/{thread_id}
```

Example:

``` json
POST /trip

{
  "query": "Plan a 4 day trip to Dubai next month under ₹80000"
}
```

Response:

``` json
{
  "thread_id": "abc123",
  "status": "awaiting_review",
  "itinerary": {}
}
```

------------------------------------------------------------------------

# 23. Error Handling

Every external tool must handle:

-   timeout
-   rate limit
-   unavailable service
-   malformed response
-   missing data
-   invalid location
-   API/network failure

Never crash the complete graph because one optional specialist failed.

Example:

``` text
Weather service unavailable.

Continue with:
- flight results
- hotel results
- budget estimate
- itinerary

and clearly mark weather as unavailable.
```

------------------------------------------------------------------------

# 24. Data Normalization

All providers should return a common internal format.

Example flight:

``` python
{
    "airline": "...",
    "origin": "...",
    "destination": "...",
    "departure": "...",
    "arrival": "...",
    "duration_minutes": 210,
    "price": 12000,
    "currency": "INR",
    "source": "...",
    "data_type": "estimated"
}
```

Example hotel:

``` python
{
    "name": "...",
    "location": "...",
    "nightly_price": 5000,
    "rating": 4.2,
    "amenities": [],
    "source": "...",
    "data_type": "estimated"
}
```

------------------------------------------------------------------------

# 25. Safety and Trust

The system should never:

-   invent a booking confirmation,
-   invent flight availability,
-   claim a hotel reservation exists,
-   claim a payment was made,
-   fabricate external sources,
-   expose hidden reasoning,
-   silently convert estimated prices into guaranteed prices.

The final answer should distinguish:

``` text
Confirmed
Estimated
Recommended
Unavailable
```

------------------------------------------------------------------------

# 26. Testing Strategy

Create tests for every layer.

## Unit tests

Test:

-   guardrail
-   budget calculations
-   date parsing
-   state updates
-   provider adapters
-   supervisor routing

## Graph tests

Test:

``` text
valid request
invalid request
weather-only request
full-trip request
budget-only modification
human approval
human rejection/change request
provider failure
```

## Demo test

Run:

``` text
"Plan a 4 day trip to Dubai next month under ₹80000"
```

Expected flow:

``` text
Guardrail
   ↓
Supervisor
   ↓
Flight + Hotel + Weather
   ↓
Budget
   ↓
Itinerary
   ↓
Human review
   ↓
Final response
```

------------------------------------------------------------------------

# 27. Manual Setup Required From the Developer

The AI coding agent should NOT pretend it can do these steps
automatically.

## Step 1 --- Install Python

Install Python 3.11 or newer.

Verify:

``` bash
python --version
```

------------------------------------------------------------------------

## Step 2 --- Install Git

Verify:

``` bash
git --version
```

------------------------------------------------------------------------

## Step 3 --- Install Ollama

Install Ollama from its official distribution.

Verify:

``` bash
ollama --version
```

------------------------------------------------------------------------

## Step 4 --- Download a local model

For example:

``` bash
ollama pull llama3.2
```

The exact model may be changed based on the user's hardware.

------------------------------------------------------------------------

## Step 5 --- Create the virtual environment

``` bash
python -m venv .venv
```

Activate it.

macOS/Linux:

``` bash
source .venv/bin/activate
```

Windows:

``` powershell
.venv\Scripts\activate
```

------------------------------------------------------------------------

## Step 6 --- Install Python dependencies

``` bash
pip install -r requirements.txt
```

------------------------------------------------------------------------

## Step 7 --- Configure environment variables

Copy:

``` text
.env.example
```

to:

``` text
.env
```

At minimum configure:

``` env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
DEMO_MODE=true
DATABASE_URL=sqlite:///./data/travel_agent.db
```

For the zero-cost demo, no paid API keys should be required.

------------------------------------------------------------------------

## Step 8 --- Run the application

For Streamlit:

``` bash
streamlit run app/main.py
```

Or if the project uses FastAPI:

``` bash
uvicorn app.main:app --reload
```

------------------------------------------------------------------------

# 28. Optional Manual Setup for Live Data

These should NOT be required for the core project.

If a developer later wants better live data:

-   configure a free-tier weather provider if necessary,
-   configure a free flight-data provider if available,
-   configure map/geocoding services,
-   configure a hotel/places provider.

Keep every provider optional.

The application must continue working in `DEMO_MODE=true`.

------------------------------------------------------------------------

# 29. What the Coding AI Must Build

The coding AI should implement the project in this order:

### Phase 1 --- Foundation

1.  Create repository.
2.  Create virtual environment instructions.
3.  Create project structure.
4.  Add requirements.
5.  Add configuration.
6.  Add logging.
7.  Add typed schemas.

### Phase 2 --- LangGraph

1.  Implement `TravelState`.
2.  Implement graph.
3.  Implement guardrail.
4.  Implement supervisor.
5.  Implement conditional routing.
6.  Implement specialist nodes.
7.  Implement human review.
8.  Implement final response node.
9.  Implement checkpointing.

### Phase 3 --- Tools

1.  Ollama tool.
2.  Weather provider.
3.  Flight provider.
4.  Hotel provider.
5.  Places provider.
6.  Routing provider.
7.  Mock providers.

### Phase 4 --- UI

1.  Streamlit interface.
2.  Workflow status.
3.  Itinerary rendering.
4.  Approval button.
5.  Change-request form.
6.  Graph resume.

### Phase 5 --- Persistence

1.  SQLite.
2.  LangGraph checkpointing.
3.  Conversation history.
4.  State persistence.

### Phase 6 --- Tests

Implement unit and graph tests.

### Phase 7 --- Documentation

Write:

-   README
-   architecture explanation
-   setup instructions
-   troubleshooting
-   provider configuration
-   demo instructions

------------------------------------------------------------------------

# 30. Coding-Agent Rules

The AI coding agent must follow these rules:

1.  **Do not use paid APIs.**
2.  **Do not require API keys for the basic demo.**
3.  **Use Ollama for local LLM inference.**
4.  **Use LangGraph for orchestration.**
5.  **Keep providers behind interfaces/adapters.**
6.  **Keep deterministic calculations outside the LLM.**
7.  **Use structured outputs wherever possible.**
8.  **Do not expose chain-of-thought.**
9.  **Do not fabricate live data.**
10. **Implement demo/mock providers.**
11. **Write tests before declaring the project complete.**
12. **Run the tests after implementation.**
13. **Do not silently skip failing tests.**
14. **Document every manual installation step.**
15. **Do not add cloud infrastructure unless explicitly requested.**
16. **Do not require Docker unless it materially simplifies setup.**
17. **Prefer SQLite over hosted PostgreSQL for the first version.**
18. **Make the entire application runnable on one developer machine.**

------------------------------------------------------------------------

# 31. Definition of Done

The project is complete when this works locally:

``` text
User enters:

"Plan a 4 day trip to Dubai next month under ₹80000."
```

The system:

``` text
1. validates request
       ↓
2. supervisor understands intent
       ↓
3. supervisor selects required agents
       ↓
4. selected agents execute
       ↓
5. results are stored in TravelState
       ↓
6. budget is calculated
       ↓
7. itinerary is generated
       ↓
8. user reviews itinerary
       ↓
9. user can approve OR request changes
       ↓
10. relevant agents run again when necessary
       ↓
11. final response is generated
       ↓
12. state/checkpoint is persisted locally
```

The system must work in:

``` env
DEMO_MODE=true
```

without requiring a paid API.

------------------------------------------------------------------------

# 32. Recommended Development Order for a Student Project

Do NOT attempt to build everything at once.

Build this minimum viable version first:

``` text
User
 ↓
Guardrail
 ↓
Supervisor
 ↓
Weather Agent
 ↓
Budget Agent
 ↓
Itinerary Agent
 ↓
Human Review
 ↓
Final Response
```

Then add:

``` text
Flight Agent
Hotel Agent
Places Agent
Routing
Persistence
```

This reduces debugging complexity dramatically.

------------------------------------------------------------------------

# 33. Architecture Review --- What Is Strong in the Original Diagram

The supplied architecture has several good decisions:

### Strong decision 1 --- Input guardrails

Validating before agent execution is correct.

### Strong decision 2 --- Supervisor

Dynamic agent selection is better than a manually defined workflow.

### Strong decision 3 --- Shared state

A common `TravelState` gives agents a predictable communication
mechanism.

### Strong decision 4 --- Human-in-the-loop

This is particularly valuable for travel planning because
recommendations involve subjective preferences.

### Strong decision 5 --- Persistence

Saving state/checkpoints enables conversations to continue after
interruptions.

------------------------------------------------------------------------

# 34. Architecture Changes Recommended

The original diagram should be adjusted in these ways.

## Change 1 --- Do not make PostgreSQL mandatory initially

Use:

``` text
SQLite
```

first.

Move to PostgreSQL only when needed.

## Change 2 --- Separate tools from agents

The agent should decide what to do.

The tool should actually call the external service.

For example:

``` text
Flight Agent
    ↓
Flight Search Tool
    ↓
Flight Provider
```

## Change 3 --- Add explicit failure paths

Every provider can fail.

Add:

``` text
Agent
  ↓
Success
  |
Failure
  ↓
Fallback / partial result
```

## Change 4 --- Add provider abstraction

Avoid locking the architecture to one MCP provider.

Use:

``` text
Agent → Interface → Provider
```

## Change 5 --- Keep arithmetic deterministic

Budget calculations should not depend on an LLM.

## Change 6 --- Add provenance

Every external result should carry:

``` text
source
timestamp
data_type
```

This improves trust.

------------------------------------------------------------------------

# 35. Final Goal

The final project should demonstrate these important agentic-AI
concepts:

-   LangGraph
-   stateful agents
-   supervisor architecture
-   dynamic routing
-   specialist agents
-   tool calling
-   structured outputs
-   conditional edges
-   parallel execution
-   human-in-the-loop
-   persistence
-   checkpointing
-   provider abstraction
-   deterministic + LLM hybrid architecture
-   error handling
-   evaluation/testing

The project should prioritize **architecture quality and explainability
over the number of APIs used**.
