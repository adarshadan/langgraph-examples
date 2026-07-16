# Chatty

A production chatbot built with LangGraph + Streamlit — persistent multi-conversation chat, LLM-generated thread labels, evals, and a full CI/CD pipeline deploying to AWS.

**Live:** [iamchatty.streamlit.app](https://iamchatty.streamlit.app)

## Features

- Multi-turn conversation via a LangGraph `StateGraph` with `SqliteSaver` checkpointing (persists across restarts, unlike in-memory checkpointers)
- Multi-conversation sidebar — switch between chat threads
- Automatic LLM-generated labels for each conversation thread
- Per-session user isolation (each browser session gets its own thread namespace)
- Dockerized and deployed to AWS (ECR + ECS Fargate + ALB, `ap-south-1`)
- CI pipeline: lint → unit tests → integration tests → LLM-as-judge evals → Docker build → push to ECR

## Structure

| Path | Purpose |
|---|---|
| `backend.py` | LangGraph workflow: state definition, chat node, label generation, thread listing |
| `frontend.py` | Streamlit UI — chat interface, sidebar thread management |
| `Dockerfile` | Container build for deployment (Streamlit on port 8501) |
| `tests/test_backend.py` | Unit tests (mocked LLM calls) |
| `tests/test_integration.py` | Integration tests against the real Groq API |
| `evals/golden_dataset.json` | Golden set of prompts + pass/fail criteria |
| `evals/run_evals.py` | LLM-as-judge eval runner — scores backend responses against the golden dataset |

## Setup

```bash
cd chatty
pip install -r requirements.txt
```

Create a `.env` file with:

```
GROQ_API_KEY=your_key_here
GROQ_MODEL=your_model_name
```

## Running locally

```bash
streamlit run frontend.py
```

## Testing & Evals

```bash
pytest tests/ -v          # unit + integration tests
python evals/run_evals.py # LLM-as-judge evals against golden_dataset.json
```

## CI/CD

`.github/workflows/chatty-ci.yml` runs on any push to `chatty/**`:

1. Lint (`ruff`)
2. Unit + integration tests (`pytest`)
3. Evals (`run_evals.py`)
4. Docker build, tag with commit SHA + `latest`
5. Push to Amazon ECR

Deployment target: ECS Fargate behind an ALB in `ap-south-1`. AWS auth currently uses long-lived IAM access keys (`AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` as repo secrets) — migrating to OIDC is a planned follow-up, along with HTTPS/ACM and an automatic deploy trigger after image push.

## Known gaps

- Browser refresh resets `session_state.user_id`, dropping the user back to a new session (fix: persist via `st.query_params`)
