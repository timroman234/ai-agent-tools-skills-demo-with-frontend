# AI Agent Tools & Skills Demo with Frontend

A demonstration of AI Agent architecture showing the difference between **Tools** and **Skills**, with a Streamlit web frontend.

## Concepts

- **Tools** = What the agent CAN DO (capabilities like `get_weather`, `get_points_of_interest`)
- **Skills** = How the agent THINKS (persona, reasoning strategy, output format)

This demo uses the "City Explorer" skill to plan day trips, calling weather and points-of-interest tools.

## Project Structure

```
├── src/agent/           # Agent logic
│   ├── agent.py         # Agentic loop with streaming + tool callbacks
│   ├── skills.py        # SkillDefinition dataclass + registry
│   └── tools.py         # get_weather, get_points_of_interest
│
├── backend/             # FastAPI wrapper
│   ├── main.py          # App entry point with CORS
│   ├── routes.py        # POST /chat/stream (SSE), GET /health
│   └── session_manager.py  # Conversation history per session
│
└── frontend/            # Streamlit app (IBM Carbon Design)
    ├── app.py           # Multi-turn chat UI
    ├── api_client.py    # SSE streaming client
    ├── components.py    # Tool + skill card renderers
    ├── config.py        # Frontend configuration
    └── styles.py        # IBM Carbon CSS
```

## Quick Start

### 1. Clone and setup

```bash
git clone https://github.com/timroman234/ai-agent-tools-skills-demo-with-frontend.git
cd ai-agent-tools-skills-demo-with-frontend
```

### 2. Create `.env` file

```bash
echo "OPENAI_API_KEY=sk-your-api-key-here" > .env
```

### 3. Install dependencies (using uv)

```bash
uv sync
```

### 4. Start the backend (Terminal 1)

```bash
uv run uvicorn backend.main:app --port 8058 --reload
```

### 5. Start the frontend (Terminal 2)

```bash
uv run streamlit run frontend/app.py
```

### 6. Try it out

Open the browser and ask:
- "Plan a day trip to Paris"
- "What should I do in Tokyo today?"
- "Recommend activities in New York"

Watch the sidebar show:
- **Active Skill** — "Day Trip Planner" with its description
- **Tools Used** — `get_weather` and `get_points_of_interest` calls

## How It Works

1. User sends a message via the Streamlit frontend
2. Frontend streams request to FastAPI backend via SSE
3. Backend runs the agentic loop:
   - Sends conversation + skill prompt to OpenAI
   - LLM decides which tools to call
   - Tools execute and return results
   - LLM generates final response
4. Backend streams events back: `session`, `skill`, `text`, `tools`, `end`
5. Frontend displays response and updates sidebar

## License

MIT
