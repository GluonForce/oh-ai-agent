# AGENTS.md

## Cursor Cloud specific instructions

### Overview

This repository is the **OH AI Agent** — an evidence-based, regulation-aligned occupational health workflow harness for the UK. It consists of:

1. **Backend** (`/workspace`) — Python/FastAPI REST API with LLM + RAG for workflow generation, benchmarking, and gap analysis.
2. **Frontend** (`/workspace/frontend`) — Next.js + shadcn/ui dashboard for interacting with the API.

### Services

| Service | Command | Port | Working Dir |
|---|---|---|---|
| Backend API | `python3 -m uvicorn oh_agent.main:app --reload --host 0.0.0.0 --port 8000` | 8000 | `/workspace` |
| Frontend Dev | `npm run dev -- -p 3000` | 3000 | `/workspace/frontend` |

No external databases required. ChromaDB runs embedded (file-based in `.chroma_db/`).

### Key commands

**Backend** (from `/workspace`):
- **Install:** `pip install -e ".[dev]"`
- **Lint:** `python3 -m ruff check src/ tests/`
- **Format:** `python3 -m ruff format src/ tests/`
- **Test:** `python3 -m pytest tests/ -v`
- **Run:** `python3 -m uvicorn oh_agent.main:app --reload --host 0.0.0.0 --port 8000`

**Frontend** (from `/workspace/frontend`):
- **Install:** `npm install`
- **Lint:** `npm run lint`
- **Build:** `npm run build`
- **Run:** `npm run dev -- -p 3000`

### LLM configuration

The LLM backend is configurable via environment variables. Set these when starting the backend:

- `OH_LLM_API_KEY` — API key (takes precedence over `OH_OPENAI_API_KEY`)
- `OH_LLM_BASE_URL` — Custom endpoint URL for any OpenAI-compatible provider
- `OH_LLM_MODEL` — Model name matching the provider (e.g. `gpt-4o`, `claude-sonnet-4-20250514`)

The `llm_client.py` factory auto-normalises base URLs: if a user pastes a full endpoint URL including `/chat/completions`, the suffix is stripped so the OpenAI SDK can append it correctly.

### Non-obvious caveats

- The `uuid7` PyPI package installs its module as `uuid_extensions`, not `uuid7`. Imports use `from uuid_extensions import uuid7`.
- The dev server auto-ingests documents from `knowledge_base/` on startup. Place `.txt`, `.md`, or `.docx` files there for RAG.
- Workflow/benchmark/gap-analysis endpoints require a working LLM API key with sufficient quota. Without it, those endpoints return 402/502. All other endpoints (health, info, knowledge, audit) work without any API key.
- The frontend connects to the backend at `http://localhost:8000` by default. Override with `NEXT_PUBLIC_API_URL` env var.
- Backend CORS is configured to allow all origins in development.
- The API docs (Swagger UI) are at `http://localhost:8000/docs`.
- Python 3.11+ is required. The environment uses Python 3.12.
- The frontend uses Next.js 16 with the app router and shadcn/ui (base-ui variant). `asChild` is not supported on Sheet/Dialog triggers — use className directly.
