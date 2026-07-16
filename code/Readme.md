# code/

LangGraph concepts, in order of increasing complexity — from a single-node graph to multi-server MCP tool calling and human-in-the-loop approval flows.

## Setup

```bash
cd code
pip install -r requirements.txt
```

Create a `.env` file in this folder (or the repo root) with:

```
GROQ_API_KEY=your_key_here
GROQ_MODEL=your_model_name
TAVILY_API_KEY=your_key_here   # only needed for 7_langgraph_tool_call.py
```

## Notebooks

| File | Concept |
|---|---|
| `0_bmi_workflow.ipynb` | Simplest possible `StateGraph` — a single node computing BMI from weight/height, no LLM involved |
| `1_simple_llm_workflow.ipynb` | Wiring a Groq LLM into a graph node; basic `TypedDict` state |
| `2_blog_generator.ipynb` | Multi-node graph: title → outline → content, with looping/list-accumulation state |
| `3_essay_evaluate_workflow.ipynb` | Structured output via Pydantic schemas; async nodes for parallel evaluation criteria |
| `4_sentiment_based_reply.ipynb` | Conditional routing — the graph branches based on classified sentiment |
| `5_linkedin_post_workflow.ipynb` | Generate → evaluate → revise loop with an iteration cap (reflection pattern) |
| `6_basic_persistant_chatbot.ipynb` | Adding `MemorySaver` checkpointing for multi-turn conversation persistence |

## Scripts

| File | Concept |
|---|---|
| `7_langgraph_tool_call.py` | Binding external tools (Tavily search) to an LLM and handling the tool-call loop manually |
| `hitl_example.py` | Human-in-the-loop: `interrupt()` + `Command` to pause a graph for external approval before proceeding |
| `langgraph_mcp_math_server.py` | An MCP server (stdio transport) exposing arithmetic tools via `fastmcp` |
| `langgraph_mcp_weather_server.py` | An MCP server (streamable-http transport) exposing a weather-lookup tool backed by wttr.in |
| `langgraph_mcp_client.py` | A LangGraph chatbot that connects to **both** MCP servers above via `MultiServerMCPClient` and routes tool calls through a standard `ToolNode` loop |
| `langgraph_mcp_hitl_client.py` | Same MCP client setup, extended with a human-in-the-loop approval step before tool execution |

## Running the MCP examples

The weather server (HTTP) must be started separately before the client connects:

```bash
# Terminal 1
python langgraph_mcp_weather_server.py

# Terminal 2
python langgraph_mcp_client.py
```

The math server (stdio) is spawned automatically by the client — no separate step needed.

**Note:** MCP server paths in `MultiServerMCPClient` should be absolute (resolved via `__file__`), not relative — relative paths resolve against the client's working directory, not the server script's location, and will fail silently as a "Connection closed" error.
