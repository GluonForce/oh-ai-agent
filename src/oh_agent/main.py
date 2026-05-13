"""FastAPI application — OH AI Agent harness.

Provides REST endpoints for:
- Workflow generation (hazard-specific, risk-profiled)
- Benchmarking against regulatory minimums
- Gap analysis
- Knowledge base management
- Audit trail inspection
- Health / readiness checks
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from oh_agent.agents.benchmark_agent import BenchmarkAgent
from oh_agent.agents.guardrails import MANDATORY_DISCLAIMERS
from oh_agent.agents.workflow_agent import WorkflowAgent
from oh_agent.config import Settings, get_settings
from oh_agent.knowledge.ingestion import ingest_directory
from oh_agent.knowledge.retriever import KnowledgeRetriever
from oh_agent.knowledge.sources import AUTHORITATIVE_SOURCES, KnowledgeSource
from oh_agent.middleware.logging import RequestLoggingMiddleware
from oh_agent.models.audit import AuditEntry
from oh_agent.models.hazard import HazardProfile
from oh_agent.models.organisation import OrganisationProfile
from oh_agent.models.workflow import (
    BenchmarkResult,
    GapAnalysis,
    WorkflowRequest,
    WorkflowResponse,
)
from oh_agent.services.audit_service import AuditService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application state (populated during lifespan)
# ---------------------------------------------------------------------------
_state: dict[str, Any] = {}


def _get_settings() -> Settings:
    return _state.get("settings") or get_settings()


def _get_retriever() -> KnowledgeRetriever:
    r = _state.get("retriever")
    if r is None:
        raise HTTPException(503, "Knowledge retriever not initialised.")
    return r  # type: ignore[return-value]


def _get_audit() -> AuditService:
    a = _state.get("audit")
    if a is None:
        raise HTTPException(503, "Audit service not initialised.")
    return a  # type: ignore[return-value]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialise shared services on startup."""
    settings = get_settings()
    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(name)s %(levelname)s %(message)s")

    retriever = KnowledgeRetriever(settings)
    audit = AuditService(settings)

    # Auto-ingest knowledge base on startup
    if settings.knowledge_dir.exists():
        count = ingest_directory(settings, retriever)
        logger.info("Ingested %d chunks from knowledge base on startup.", count)

    _state["settings"] = settings
    _state["retriever"] = retriever
    _state["audit"] = audit

    logger.info("OH AI Agent started (env=%s, model=%s).", settings.environment.value, settings.llm_model)
    yield
    logger.info("OH AI Agent shutting down.")


app = FastAPI(
    title="OH AI Agent",
    version="0.1.0",
    description=(
        "Evidence-based, regulation-aligned occupational health workflow harness. "
        "Designed for highly regulated UK healthcare environments."
    ),
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health & info endpoints
# ---------------------------------------------------------------------------


class HealthResponse(BaseModel):
    status: str = "healthy"
    environment: str
    knowledge_chunks: int
    audit_entries: int


@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health() -> HealthResponse:
    settings = _get_settings()
    retriever = _get_retriever()
    audit = _get_audit()
    return HealthResponse(
        environment=settings.environment.value,
        knowledge_chunks=retriever.collection_count,
        audit_entries=audit.count(),
    )


@app.get("/info", tags=["system"])
async def info() -> dict[str, Any]:
    settings = _get_settings()
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "llm_model": settings.llm_model,
        "disclaimers": MANDATORY_DISCLAIMERS,
    }


# ---------------------------------------------------------------------------
# Workflow endpoints
# ---------------------------------------------------------------------------


@app.post("/api/v1/workflows", response_model=WorkflowResponse, tags=["workflows"])
async def generate_workflow(request: WorkflowRequest) -> WorkflowResponse:
    """Generate a hazard-specific, risk-profiled OH workflow."""
    settings = _get_settings()
    retriever = _get_retriever()
    audit_svc = _get_audit()

    agent = WorkflowAgent(settings=settings, retriever=retriever)
    response, audit_entries = agent.generate(request)
    audit_svc.log_many(audit_entries)
    return response


# ---------------------------------------------------------------------------
# Benchmark & gap analysis endpoints
# ---------------------------------------------------------------------------


class BenchmarkRequest(BaseModel):
    organisation: OrganisationProfile
    hazards: list[HazardProfile] = Field(..., min_length=1)


@app.post("/api/v1/benchmark", response_model=BenchmarkResult, tags=["assurance"])
async def benchmark(request: BenchmarkRequest) -> BenchmarkResult:
    """Benchmark current practice against regulatory minimums."""
    settings = _get_settings()
    retriever = _get_retriever()
    audit_svc = _get_audit()

    agent = BenchmarkAgent(settings=settings, retriever=retriever)
    result, audit_entries = agent.benchmark(request.organisation, request.hazards)
    audit_svc.log_many(audit_entries)
    return result


@app.post("/api/v1/gap-analysis", response_model=GapAnalysis, tags=["assurance"])
async def gap_analysis(request: BenchmarkRequest) -> GapAnalysis:
    """Perform structured gap analysis against regulatory requirements."""
    settings = _get_settings()
    retriever = _get_retriever()
    audit_svc = _get_audit()

    agent = BenchmarkAgent(settings=settings, retriever=retriever)
    result, audit_entries = agent.gap_analysis(request.organisation, request.hazards)
    audit_svc.log_many(audit_entries)
    return result


# ---------------------------------------------------------------------------
# Knowledge management endpoints
# ---------------------------------------------------------------------------


@app.get("/api/v1/knowledge/sources", response_model=list[KnowledgeSource], tags=["knowledge"])
async def list_sources() -> list[KnowledgeSource]:
    """List pre-registered authoritative sources."""
    return AUTHORITATIVE_SOURCES


class KnowledgeStats(BaseModel):
    total_chunks: int
    sources_registered: int


@app.get("/api/v1/knowledge/stats", response_model=KnowledgeStats, tags=["knowledge"])
async def knowledge_stats() -> KnowledgeStats:
    retriever = _get_retriever()
    return KnowledgeStats(
        total_chunks=retriever.collection_count,
        sources_registered=len(AUTHORITATIVE_SOURCES),
    )


class IngestResponse(BaseModel):
    chunks_ingested: int
    message: str


@app.post("/api/v1/knowledge/ingest", response_model=IngestResponse, tags=["knowledge"])
async def ingest_knowledge() -> IngestResponse:
    """Re-ingest all documents from the knowledge_base directory."""
    settings = _get_settings()
    retriever = _get_retriever()
    audit_svc = _get_audit()

    count = ingest_directory(settings, retriever)
    audit_svc.log(
        AuditEntry(
            event_type="document_ingested",  # type: ignore[arg-type]
            detail={"chunks_ingested": count, "source": "knowledge_base"},
        )
    )
    return IngestResponse(chunks_ingested=count, message=f"Ingested {count} chunks from knowledge base.")


@app.post("/api/v1/knowledge/upload", response_model=IngestResponse, tags=["knowledge"])
async def upload_document(file: UploadFile) -> IngestResponse:
    """Upload a single document to the knowledge base and ingest it."""
    settings = _get_settings()
    retriever = _get_retriever()
    audit_svc = _get_audit()

    if not file.filename:
        raise HTTPException(400, "Filename is required.")

    allowed = {".txt", ".md", ".docx"}
    suffix = Path(file.filename).suffix.lower()
    if suffix not in allowed:
        raise HTTPException(400, f"Unsupported file type '{suffix}'. Allowed: {allowed}")

    dest = settings.knowledge_dir / file.filename
    settings.knowledge_dir.mkdir(parents=True, exist_ok=True)
    content = await file.read()
    dest.write_bytes(content)

    count = ingest_directory(settings, retriever, directory=settings.knowledge_dir)
    audit_svc.log(
        AuditEntry(
            event_type="document_ingested",  # type: ignore[arg-type]
            detail={"filename": file.filename, "chunks_ingested": count},
        )
    )
    return IngestResponse(chunks_ingested=count, message=f"Uploaded and ingested '{file.filename}' ({count} chunks).")


# ---------------------------------------------------------------------------
# Audit trail endpoints
# ---------------------------------------------------------------------------


@app.get("/api/v1/audit", response_model=list[AuditEntry], tags=["audit"])
async def get_audit_trail(limit: int = 100) -> list[AuditEntry]:
    """Retrieve recent audit trail entries."""
    audit_svc = _get_audit()
    entries = audit_svc.read_all()
    return entries[-limit:]


@app.get("/api/v1/audit/count", tags=["audit"])
async def audit_count() -> dict[str, int]:
    audit_svc = _get_audit()
    return {"total_entries": audit_svc.count()}
