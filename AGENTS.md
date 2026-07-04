# AGENTS.md

## Cursor Cloud specific instructions

### Overview

This repository is the **OH AI Agent** — an evidence-based, regulation-aligned occupational health workflow harness for the UK. It consists of:

1. **Backend** (`/workspace`) — Python/FastAPI REST API with LLM + RAG for workflow generation, benchmarking, and gap analysis.
2. **Frontend** (`/workspace/frontend`) — Next.js + shadcn/ui dashboard for interacting with the API.

### Services

| Service | Command | Port | Working Dir |
|---|---|---|---|
| Backend API | `uv run uvicorn oh_agent.main:app --reload --host 0.0.0.0 --port 8000` | 8000 | repo root |
| Frontend Dev | `npm run dev -- -p 3000` | 3000 | `/workspace/frontend` |

No external databases required. ChromaDB runs embedded (file-based in `.chroma_db/`).

### Key commands

**Backend** (from repo root; uses [uv](https://docs.astral.sh/uv/)):
- **Install:** `uv sync`
- **Lint:** `uv run ruff check src/ tests/`
- **Format:** `uv run ruff format src/ tests/`
- **Test:** `uv run pytest tests/ -v`
- **Run:** `uv run uvicorn oh_agent.main:app --reload --host 0.0.0.0 --port 8000`

**Frontend** (from `/workspace/frontend`):
- **Install:** `npm install`
- **Lint:** `npm run lint`
- **Build:** `npm run build`
- **Run:** `npm run dev -- -p 3000`

### LLM configuration

Chat completions use **LiteLLM** by default (`OH_LLM_PROVIDER=litellm`). Switch models with `OH_LLM_MODEL` only.

- `OH_LLM_PROVIDER` — `litellm` | `openrouter` | `openai` (legacy SDK)
- `OH_LLM_API_KEY` — API key (takes precedence over `OH_OPENAI_API_KEY`)
- `OH_LLM_MODEL` — e.g. `gpt-4o`, or with OpenRouter preset `anthropic/claude-sonnet-4`
- `OH_LLM_BASE_URL` — optional; OpenRouter preset defaults to `https://openrouter.ai/api/v1`

`GET /info` exposes `llm_resolved_model`. Base URLs pasted with `/chat/completions` are normalised automatically.

### Non-obvious caveats

- The `uuid7` PyPI package installs its module as `uuid_extensions`, not `uuid7`. Imports use `from uuid_extensions import uuid7`.
- The dev server auto-ingests documents from `knowledge_base/` on startup. Place `.txt`, `.md`, or `.docx` files there for RAG.
- Workflow/benchmark/gap-analysis endpoints require a working LLM API key with sufficient quota. Without it, those endpoints return 402/502. All other endpoints (health, info, knowledge, audit) work without any API key.
- The frontend connects to the backend at `http://localhost:8000` by default. Override with `NEXT_PUBLIC_API_URL` env var.
- Production deploy (Vercel + Railway): see [docs/DEPLOY_VERCEL_RAILWAY.md](docs/DEPLOY_VERCEL_RAILWAY.md).
- Backend CORS is configured to allow all origins in development.
- The API docs (Swagger UI) are at `http://localhost:8000/docs`.
- Python 3.11+ is required. The environment uses Python 3.12.
- The frontend uses Next.js 16 with the app router and shadcn/ui (base-ui variant). `asChild` is not supported on Sheet/Dialog triggers — use className directly.
