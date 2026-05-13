# AGENTS.md

## Cursor Cloud specific instructions

### Overview

This repository is the **OH AI Agent** — an evidence-based, regulation-aligned occupational health workflow harness for the UK. It is a Python/FastAPI application that uses LLM + RAG to generate hazard-specific OH workflows, benchmark current practice, and perform gap analyses against UK regulatory minimums.

### Services

| Service | Command | Port |
|---|---|---|
| API Server | `python3 -m uvicorn oh_agent.main:app --reload --host 0.0.0.0 --port 8000` | 8000 |

There are no external database dependencies. ChromaDB runs embedded (file-based in `.chroma_db/`).

### Key commands

See `README.md` and `pyproject.toml` for full details. Quick reference:

- **Install:** `pip install -e ".[dev]"`
- **Lint:** `python3 -m ruff check src/ tests/`
- **Format:** `python3 -m ruff format src/ tests/`
- **Test:** `python3 -m pytest tests/ -v`
- **Run dev server:** `python3 -m uvicorn oh_agent.main:app --reload --host 0.0.0.0 --port 8000`

### Non-obvious caveats

- The `uuid7` PyPI package installs its module as `uuid_extensions`, not `uuid7`. Imports should use `from uuid_extensions import uuid7`.
- The dev server auto-ingests documents from `knowledge_base/` on startup. Place `.txt`, `.md`, or `.docx` files there.
- Workflow/benchmark/gap-analysis endpoints require a valid `OH_OPENAI_API_KEY` env var to call the LLM. Without it, those endpoints will fail. All other endpoints (health, info, knowledge, audit) work without an API key.
- The API docs (Swagger UI) are at `/docs` when the server is running.
- Python 3.11+ is required. The environment uses Python 3.12.
