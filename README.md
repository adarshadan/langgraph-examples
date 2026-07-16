# LangGraph Examples

A personal learning-to-production repo for [LangGraph](https://github.com/langchain-ai/langgraph) — starting from basic stateful graphs and building up to a deployed, CI/CD-backed AI chatbot.

## Repo Structure

| Folder | What it is |
|---|---|
| [`code/`](./code) | Notebooks and scripts covering core LangGraph concepts — state graphs, conditional routing, tool calling, MCP integration, and human-in-the-loop patterns |
| [`chatty/`](./chatty) | **Chatty** — a production chatbot built with LangGraph + Streamlit, with persistence, evals, and a full CI/CD pipeline to AWS |
| `.devcontainer/` | Dev container config for a consistent local environment |

Each folder has its own `README.md` with setup and usage details specific to it.

## Tech Stack

- **Orchestration:** LangGraph (`StateGraph`, conditional edges, checkpointers)
- **LLM:** Groq (via `langchain-groq`)
- **UI:** Streamlit
- **Tooling protocol:** MCP (Model Context Protocol) via `fastmcp` and `langchain-mcp-adapters`
- **Persistence:** SQLite (`langgraph-checkpoint-sqlite`), in-memory checkpointers for simpler examples

## Getting Started

```bash
git clone https://github.com/adarshadan/langgraph-examples.git
cd langgraph-examples
pip install -r requirements.txt
```

Most examples expect a `.env` file with:

```
GROQ_API_KEY=your_key_here
GROQ_MODEL=your_model_name
```

See the folder-level READMEs for anything beyond that (e.g. Tavily keys for search tools, or AWS setup for Chatty's deployment).

## About

Built by [Adarsha Dan](https://github.com/adarshadan) — an AI Engineer transitioning from 12+ years in enterprise RPA (UiPath, Automation Anywhere, Blue Prism) into agentic AI systems.
