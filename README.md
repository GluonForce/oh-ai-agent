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

## Quick Start

### Prerequisites

- Python 3.11+
- An API key for any OpenAI-compatible LLM provider

### Installation

```bash
# Clone and install (development mode)
pip install -e ".[dev]"

# Copy environment config
cp .env.example .env
# Edit .env — see "LLM Provider Configuration" below
```

### Run the Development Server

```bash
uvicorn oh_agent.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### LLM Provider Configuration

The agent works with **any OpenAI-compatible API**. Set these environment variables in `.env`:

| Variable | Description |
|---|---|
| `OH_LLM_API_KEY` | Your API key (takes precedence over `OH_OPENAI_API_KEY`) |
| `OH_LLM_BASE_URL` | Custom endpoint URL (leave empty for OpenAI) |
| `OH_LLM_MODEL` | Model identifier matching your provider |

**Provider examples:**

```bash
# OpenAI (default)
OH_LLM_API_KEY=sk-...
OH_LLM_MODEL=gpt-4o

# OpenRouter (access to many models)
OH_LLM_API_KEY=sk-or-...
OH_LLM_BASE_URL=https://openrouter.ai/api/v1
OH_LLM_MODEL=anthropic/claude-sonnet-4

# Anthropic direct
OH_LLM_API_KEY=sk-ant-...
OH_LLM_BASE_URL=https://api.anthropic.com/v1
OH_LLM_MODEL=claude-sonnet-4-20250514

# Groq (fast inference)
OH_LLM_API_KEY=gsk_...
OH_LLM_BASE_URL=https://api.groq.com/openai/v1
OH_LLM_MODEL=llama-3.3-70b-versatile

# Local Ollama
OH_LLM_BASE_URL=http://localhost:11434/v1
OH_LLM_MODEL=llama3
OH_LLM_API_KEY=ollama
```

### Run Tests

```bash
pytest
```

### Lint & Type Check

```bash
ruff check src/ tests/
ruff format --check src/ tests/
mypy src/
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
src/oh_agent/
├── main.py                 # FastAPI application
├── config.py               # Configuration (env-var driven)
├── models/                 # Pydantic domain models
│   ├── hazard.py           # Hazard & exposure models
│   ├── organisation.py     # Organisation profile
│   ├── workflow.py         # Workflow, benchmark, gap analysis
│   └── audit.py            # Audit trail
├── agents/                 # Agent logic
│   ├── workflow_agent.py   # Workflow generation (LLM + RAG)
│   ├── benchmark_agent.py  # Benchmarking & gap analysis
│   └── guardrails.py       # Compliance guardrails
├── knowledge/              # Knowledge/RAG layer
│   ├── retriever.py        # ChromaDB vector retrieval
│   ├── ingestion.py        # Document ingestion pipeline
│   └── sources.py          # Authoritative source registry
├── services/
│   └── audit_service.py    # Audit logging service
└── middleware/
    └── logging.py          # HTTP request logging
```

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

## License

MIT
