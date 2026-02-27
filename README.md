# Headless Autonomous Support Agent

A production-ready, stateful AI agent architecture that autonomously routes queries, executes external tools, and maintains persistent thread-based memory across disconnected HTTP requests.

🚀 **[Test the Live API Here (Swagger UI)](INSERT_YOUR_RENDER_URL_HERE/docs)** 🎥 **[Watch the 60-Second Architecture Demo Here](INSERT_YOUR_LOOM_LINK_HERE)**

> **Note to Recruiters & Reviewers:** This live demo is hosted on a free Render instance. If the server has been asleep, **the very first request may take up to 50 seconds to process** while the container wakes up. All subsequent requests will process in milliseconds.

## System Architecture

This project abandons the standard "stateless API wrapper" approach in favor of a deterministic, graph-based state machine wired directly into a cloud database for long-term memory. 

* **Routing & Logic:** [LangGraph](https://python.langchain.com/v0.1/docs/langgraph/) (ReAct cyclic graph for deterministic tool execution and conversational fallback).
* **Inference:** Meta Llama 3.3 via Groq API (chosen for ultra-low latency processing).
* **State Management:** Fully Asynchronous PostgreSQL (hosted on Neon) via `psycopg` `AsyncConnectionPool` and LangGraph's `AsyncPostgresSaver`. Solves the stateless nature of HTTP by binding graph memory to unique session `thread_id`s without blocking the event loop.
* **API Framework:** FastAPI (chosen for high-performance async routing and automatic OpenAPI documentation).

## Key Features

1.  **Multi-Tool Autonomy:** The agent intelligently routes between checking external databases (Inventory Check) and querying transaction states (Refund Status) based strictly on conversational context.
2.  **Persistent Database Memory:** Survives server reboots and stateless HTTP calls. The agent recalls variables (like product SKUs and user names) from past requests by querying the Postgres checkpointer.
3.  **Strict Persona Constraints:** Implements system-level prompt injection to prevent the agent from hallucinating or answering out-of-domain queries.

---

## Local Development Quickstart

If you wish to run this architecture locally:

```bash
git clone [https://github.com/Jade7107/headless-support-agent.git](https://github.com/Jade7107/headless-support-agent.git)
cd headless-support-agent

# 1. Build the local Postgres container
docker compose up -d

# 2. Install dependencies
py -m pip install -r requirements.txt

# 3. Ignite the server
py -m uvicorn app.main:app --reload
Navigate to http://localhost:8000/ to access the interactive Swagger UI.