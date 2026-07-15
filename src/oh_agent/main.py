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

import asyncio
import logging
import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from oh_agent.agents.benchmark_agent import (
    BenchmarkAgent,
    ComplianceAuditAgent,
    ImprovementPlanAgent,
    TrendAnalysisAgent,
)
from oh_agent.agents.guardrails import MANDATORY_DISCLAIMERS, GuardrailViolation
from oh_agent.agents.llm_client import create_llm_client
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
    ComplianceAuditRequest,
    ComplianceAuditResponse,
    GapAnalysis,
    ImprovementPlanRequest,
    ImprovementPlanResponse,
    TrendAnalysisRequest,
    TrendAnalysisResponse,
    WorkflowRequest,
    WorkflowResponse,
)
from oh_agent.privacy.pii_masking import (
    mask_compliance_request,
    mask_improvement_request,
    mask_org_hazards,
    mask_text,
    mask_trend_request,
    mask_workflow_request,
)
from oh_agent.services.audit_service import AuditService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application state (populated during lifespan)
# ---------------------------------------------------------------------------
_state: dict[str, Any] = {}
_retriever_lock = threading.Lock()
_audit_lock = threading.Lock()


def _get_settings() -> Settings:
    return _state.get("settings") or get_settings()


def _get_retriever() -> KnowledgeRetriever:
    """Lazy-init ChromaDB on first use (avoids ~80MB model download on boot)."""
    r = _state.get("retriever")
    if r is not None:
        return r  # type: ignore[return-value]
    with _retriever_lock:
        r = _state.get("retriever")
        if r is not None:
            return r  # type: ignore[return-value]
        settings = _get_settings()
        logger.info("Initialising knowledge store (first use; may take a moment)...")
        r = KnowledgeRetriever(settings)
        _state["retriever"] = r
        return r  # type: ignore[return-value]


def _get_audit() -> AuditService:
    a = _state.get("audit")
    if a is not None:
        return a  # type: ignore[return-value]
    with _audit_lock:
        a = _state.get("audit")
        if a is not None:
            return a  # type: ignore[return-value]
        a = AuditService(_get_settings())
        _state["audit"] = a
        return a  # type: ignore[return-value]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Minimal startup — heavy services load on first request."""
    settings = get_settings()
    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    _state["settings"] = settings

    async def maybe_ingest() -> None:
        if not settings.ingest_on_startup or not settings.knowledge_dir.exists():
            return
        try:
            retriever = await asyncio.to_thread(_get_retriever)
            count = await asyncio.to_thread(ingest_directory, settings, retriever)
            logger.info("Ingested %d chunks from knowledge base on startup.", count)
        except Exception:
            logger.exception("Knowledge base ingestion failed on startup.")

    ingest_task = asyncio.create_task(maybe_ingest())

    logger.info("OH AI Agent listening (env=%s, model=%s).", settings.environment.value, settings.llm_model)
    yield

    ingest_task.cancel()
    with suppress(asyncio.CancelledError):
        await ingest_task
    logger.info("OH AI Agent shutting down.")


app = FastAPI(
    title="OH AI Agent",
    version="0.2.0",
    description=(
        "Evidence-based, regulation-aligned occupational health workflow harness "
        "structured around the Plan-Do-Check-Act (PDCA) framework. "
        "Designed for highly regulated UK healthcare environments."
    ),
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
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
    settings = _state.get("settings") or get_settings()
    retriever = _state.get("retriever")
    audit = _state.get("audit")
    return HealthResponse(
        environment=settings.environment.value,
        knowledge_chunks=retriever.collection_count if retriever else 0,
        audit_entries=audit.count() if audit else 0,
    )


@app.get("/info", tags=["system"])
async def info() -> dict[str, Any]:
    settings = _get_settings()
    llm = create_llm_client(settings)
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "framework": "PDCA (Plan-Do-Check-Act)",
        "llm_provider": settings.llm_provider.value,
        "llm_model": settings.llm_model,
        "llm_resolved_model": llm.resolved_model,
        "disclaimers": MANDATORY_DISCLAIMERS,
    }


# ---------------------------------------------------------------------------
# Workflow endpoints
# ---------------------------------------------------------------------------


def _handle_llm_error(exc: Exception) -> None:
    if isinstance(exc, GuardrailViolation):
        raise HTTPException(
            422,
            {
                "detail": "Generated output blocked by compliance guardrails.",
                "violations": exc.violations,
            },
        ) from exc
    msg = str(exc)
    if "insufficient_quota" in msg or "exceeded" in msg.lower():
        raise HTTPException(402, f"LLM quota exceeded: {msg}") from exc
    if "risk assessment must be confirmed" in msg.lower() or "worker consultation" in msg.lower():
        raise HTTPException(422, str(exc)) from exc
    raise HTTPException(502, f"LLM request failed: {msg}") from exc


@app.post("/api/v1/workflows", response_model=WorkflowResponse, tags=["workflows"])
async def generate_workflow(request: WorkflowRequest) -> WorkflowResponse:
    """Generate a hazard-specific, risk-profiled OH workflow."""
    settings = _get_settings()
    request = mask_workflow_request(request, settings)
    retriever = _get_retriever()
    audit_svc = _get_audit()

    agent = WorkflowAgent(settings=settings, retriever=retriever)
    try:
        response, audit_entries = agent.generate(request)
    except Exception as exc:
        _handle_llm_error(exc)
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
    org, hazards = mask_org_hazards(request.organisation, request.hazards, settings)
    retriever = _get_retriever()
    audit_svc = _get_audit()

    agent = BenchmarkAgent(settings=settings, retriever=retriever)
    try:
        result, audit_entries = agent.benchmark(org, hazards)
    except Exception as exc:
        _handle_llm_error(exc)
    audit_svc.log_many(audit_entries)
    return result


@app.post("/api/v1/gap-analysis", response_model=GapAnalysis, tags=["assurance"])
async def gap_analysis(request: BenchmarkRequest) -> GapAnalysis:
    """Perform structured gap analysis against regulatory requirements."""
    settings = _get_settings()
    org, hazards = mask_org_hazards(request.organisation, request.hazards, settings)
    retriever = _get_retriever()
    audit_svc = _get_audit()

    agent = BenchmarkAgent(settings=settings, retriever=retriever)
    try:
        result, audit_entries = agent.gap_analysis(org, hazards)
    except Exception as exc:
        _handle_llm_error(exc)
    audit_svc.log_many(audit_entries)
    return result


# ---------------------------------------------------------------------------
# CHECK — Compliance Audit
# ---------------------------------------------------------------------------


@app.post("/api/v1/compliance-audit", response_model=ComplianceAuditResponse, tags=["check"])
async def compliance_audit(request: ComplianceAuditRequest) -> ComplianceAuditResponse:
    """Evaluate statutory OH compliance (CHECK phase)."""
    settings = _get_settings()
    request = mask_compliance_request(request, settings)
    retriever = _get_retriever()
    audit_svc = _get_audit()
    agent = ComplianceAuditAgent(settings=settings, retriever=retriever)
    try:
        result, audit_entries = agent.audit(request.organisation, request.hazards)
    except Exception as exc:
        _handle_llm_error(exc)
    audit_svc.log_many(audit_entries)
    return result


# ---------------------------------------------------------------------------
# REVIEW — Trend Analysis
# ---------------------------------------------------------------------------


@app.post("/api/v1/trend-analysis", response_model=TrendAnalysisResponse, tags=["review"])
async def trend_analysis(request: TrendAnalysisRequest) -> TrendAnalysisResponse:
    """Analyse anonymised surveillance data for trends (REVIEW phase)."""
    settings = _get_settings()
    request = mask_trend_request(request, settings)
    retriever = _get_retriever()
    audit_svc = _get_audit()
    agent = TrendAnalysisAgent(settings=settings, retriever=retriever)
    try:
        result, audit_entries = agent.analyse(request.organisation, request.hazards, request.surveillance_summary)
    except Exception as exc:
        _handle_llm_error(exc)
    audit_svc.log_many(audit_entries)
    return result


# ---------------------------------------------------------------------------
# ACT — Improvement Plan
# ---------------------------------------------------------------------------


@app.post("/api/v1/improvement-plan", response_model=ImprovementPlanResponse, tags=["act"])
async def improvement_plan(request: ImprovementPlanRequest) -> ImprovementPlanResponse:
    """Generate improvement actions from surveillance findings (ACT phase)."""
    settings = _get_settings()
    request = mask_improvement_request(request, settings)
    retriever = _get_retriever()
    audit_svc = _get_audit()
    agent = ImprovementPlanAgent(settings=settings, retriever=retriever)
    try:
        result, audit_entries = agent.plan(request.organisation, request.hazards, request.surveillance_findings)
    except Exception as exc:
        _handle_llm_error(exc)
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
    if suffix in {".txt", ".md"}:
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.decode("latin-1", errors="replace")
        masked = mask_text(text, settings)
        content = (masked or text).encode("utf-8")
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
