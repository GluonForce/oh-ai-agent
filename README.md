# OH AI Agent

**Evidence-based, regulation-aligned occupational health workflow harness for the UK.**

An open-access AI Agent that supports occupational health (OH) practitioners in generating hazard-specific, risk-profiled, evidence-based, and regulatory-compliant OH workflows. Designed for use in highly regulated healthcare environments, the agent draws exclusively from authoritative sources (HSE guidance, ACoPs, peer-reviewed literature) and never makes clinical decisions.

---

## Key Capabilities

| Capability | Description |
|---|---|
| **Workflow Generation** | Hazard-specific, risk-profiled workflows tailored to organisation context |
| **Benchmarking** | Compare current practice against UK regulatory minimums |
| **Gap Analysis** | Structured gap analysis with actionable recommendations |
| **Knowledge Base** | RAG-powered retrieval from authoritative OH sources |
| **Audit Trail** | Immutable JSONL audit log for full traceability |
| **Compliance Guardrails** | Automated checks preventing clinical decisions in outputs |

## What the Agent Will NOT Do

- Make clinical decisions or provide a diagnosis
- Offer personalised medical advice
- Replace professional judgement of qualified OH practitioners
- Transfer accountability from duty holders
- Replace risk assessment, exposure monitoring, or hierarchy of controls

---

## Quick Start (Local Setup)

**New to Python or on Windows?** See the step-by-step guide for running from a zip file: [docs/LOCAL_SETUP.md](docs/LOCAL_SETUP.md).

### Prerequisites

- Python 3.11+ and [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Node.js 18+ and npm
- An API key for any OpenAI-compatible LLM provider

### 1. Clone the Repository

```bash
git clone https://github.com/GluonForce/oh-ai-agent.git
cd oh-ai-agent
```

### 2. Backend Setup

```bash
# Install Python dependencies (creates .venv, includes dev tools)
uv sync

# Copy environment config
cp .env.example .env
# Edit .env and set your LLM API key — see "LLM Provider Configuration" below
```

### 3. Frontend Setup

```bash
cd frontend
npm install
cd ..
```

### 4. Start the Backend

```bash
uv run uvicorn oh_agent.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. Interactive API docs (Swagger UI) at `http://localhost:8000/docs`.

### 5. Start the Frontend (in a separate terminal)

```bash
cd frontend
npm run dev
```

The UI will be available at `http://localhost:3000`.

### All-in-One (both services)

```bash
# Terminal 1 — Backend
uv run uvicorn oh_agent.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — Frontend
cd frontend && npm run dev
```

### LLM Provider Configuration

Chat completions use **[LiteLLM](https://docs.litellm.ai/)** by default so you can switch models via environment variables only. Set these in `.env`:

| Variable | Description |
|---|---|
| `OH_LLM_PROVIDER` | `litellm` (default), `openrouter`, or `openai` (legacy OpenAI SDK only) |
| `OH_LLM_API_KEY` | API key (takes precedence over `OH_OPENAI_API_KEY`) |
| `OH_LLM_MODEL` | Model id for your provider |
| `OH_LLM_BASE_URL` | Optional API base (OpenRouter preset fills this automatically) |

`GET /info` returns `llm_provider`, `llm_model`, and `llm_resolved_model` (the id actually sent to the API).

**Examples:**

```bash
# OpenAI
OH_LLM_PROVIDER=litellm
OH_LLM_API_KEY=sk-...
OH_LLM_MODEL=gpt-4o

# OpenRouter (recommended preset — prefixes model with openrouter/)
OH_LLM_PROVIDER=openrouter
OH_LLM_API_KEY=sk-or-v1-...
OH_LLM_MODEL=anthropic/claude-sonnet-4

# Groq
OH_LLM_PROVIDER=litellm
OH_LLM_API_KEY=gsk_...
OH_LLM_MODEL=groq/llama-3.3-70b-versatile

# Local Ollama
OH_LLM_PROVIDER=litellm
OH_LLM_BASE_URL=http://localhost:11434/v1
OH_LLM_MODEL=ollama/llama3
OH_LLM_API_KEY=ollama
```

### Python tooling (uv)

This project uses [uv](https://docs.astral.sh/uv/) for dependencies. Commit `uv.lock` with application changes.

```bash
uv sync              # install / update .venv (includes dev tools)
uv add <package>     # add a runtime dependency
uv add --dev <pkg>   # add a dev dependency
uv lock              # refresh lockfile after editing pyproject.toml
uv run <command>     # run a command inside the project venv
```

### Run Tests

```bash
# Backend tests
uv run pytest

# Frontend lint
cd frontend && npm run lint
```

### Lint & Type Check

```bash
# Backend
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run mypy src/

# Frontend
cd frontend && npm run lint && npm run build
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check with system status |
| `GET` | `/info` | Application info and disclaimers |
| `POST` | `/api/v1/workflows` | Generate an OH workflow |
| `POST` | `/api/v1/benchmark` | Benchmark against regulatory minimums |
| `POST` | `/api/v1/gap-analysis` | Structured gap analysis |
| `GET` | `/api/v1/knowledge/sources` | List authoritative sources |
| `GET` | `/api/v1/knowledge/stats` | Knowledge base statistics |
| `POST` | `/api/v1/knowledge/ingest` | Re-ingest knowledge base documents |
| `POST` | `/api/v1/knowledge/upload` | Upload a document to knowledge base |
| `GET` | `/api/v1/audit` | Retrieve audit trail entries |
| `GET` | `/api/v1/audit/count` | Count audit entries |

---

## Project Structure

```
oh-ai-agent/
├── src/oh_agent/               # Backend (Python/FastAPI)
│   ├── main.py                 # FastAPI application & endpoints
│   ├── config.py               # Configuration (env-var driven)
│   ├── models/                 # Pydantic domain models
│   │   ├── hazard.py           # Hazard & exposure models
│   │   ├── organisation.py     # Organisation profile
│   │   ├── workflow.py         # Workflow, benchmark, gap analysis
│   │   └── audit.py            # Audit trail
│   ├── agents/                 # Agent logic
│   │   ├── workflow_agent.py   # Workflow generation (LLM + RAG)
│   │   ├── benchmark_agent.py  # Benchmarking & gap analysis
│   │   ├── llm_client.py       # Multi-provider LLM client factory
│   │   └── guardrails.py       # Compliance guardrails
│   ├── knowledge/              # Knowledge/RAG layer
│   │   ├── retriever.py        # ChromaDB vector retrieval
│   │   ├── ingestion.py        # Document ingestion pipeline
│   │   └── sources.py          # Authoritative source registry
│   ├── services/
│   │   └── audit_service.py    # Audit logging service
│   └── middleware/
│       └── logging.py          # HTTP request logging
├── frontend/                   # Frontend (Next.js + shadcn/ui)
│   └── src/
│       ├── app/                # Pages (dashboard, workflows, benchmark, etc.)
│       ├── components/         # Shared UI components & shadcn/ui
│       └── lib/                # API client, types, utilities
├── tests/                      # Backend test suite (pytest)
├── knowledge_base/             # Drop authoritative documents here
├── pyproject.toml              # Python project config & dependencies
├── Dockerfile                  # Production container
└── .env.example                # Environment variable template
```

---

## Frontend

The frontend is a Next.js application using [shadcn/ui](https://ui.shadcn.com/) components, providing a professional healthcare-appropriate interface.

| Page | Description |
|---|---|
| **Dashboard** | System health, knowledge stats, audit count, mandatory disclaimers |
| **Workflow Generator** | Organisation + hazard input form → generated workflow steps table |
| **Benchmarking** | Compliance/non-compliance breakdown with recommendations |
| **Gap Analysis** | Structured gap table with ratings and regulatory references |
| **Knowledge Base** | Browse sources, view stats, upload documents, re-ingest |
| **Audit Trail** | Color-coded event log with timestamps for regulatory traceability |

The frontend connects to the backend at `http://localhost:8000` by default. To change this, set the `NEXT_PUBLIC_API_URL` environment variable before starting the frontend.

---

## Knowledge Base

Place authoritative documents (`.txt`, `.md`, `.docx`) in the `knowledge_base/` directory. They will be automatically chunked, embedded, and indexed on startup. The agent uses retrieval-augmented generation (RAG) to ground outputs in these sources.

Pre-registered authoritative sources include HSE guidance (HSG61, EH40, COSHH Essentials), ACoPs (L108, L140), and Faculty of Occupational Medicine standards.

---

## Regulatory Alignment

This agent is designed for deployment in regulated UK healthcare environments. All outputs include:

- **Source citations** traceable to authoritative publications
- **Mandatory disclaimers** clarifying scope boundaries
- **Governance prompts** for safe delegation and supervision
- **Full audit trail** of every action for regulatory inspection

---

## Deployment (Vercel + Railway)

To share a URL with end users, deploy the **backend on Railway** and the **frontend on Vercel**:

- **Backend:** root `Dockerfile` + persistent volume at `/app/data`
- **Frontend:** `frontend/` with `NEXT_PUBLIC_API_URL` pointing at your Railway URL

Full step-by-step instructions: **[docs/DEPLOY_VERCEL_RAILWAY.md](docs/DEPLOY_VERCEL_RAILWAY.md)**

---

## License

MIT
