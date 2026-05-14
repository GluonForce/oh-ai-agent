"""FastAPI application — OH AI Agent harness (PDCA framework).

Provides REST endpoints structured around the PDCA cycle:
- PLAN: Risk assessment confirmation + workflow generation
- DO: Statutory OH provision (surveillance, competence, referrals)
- CHECK: Compliance audit (employee coverage, intervals, governance)
- REVIEW: Trend analysis of anonymised surveillance data
- ACT: Improvement actions feeding back into risk management
- Knowledge base management
- Audit trail inspection
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from oh_agent.agents.benchmark_agent import (
    ComplianceAuditAgent,
    ImprovementPlanAgent,
    TrendAnalysisAgent,
)
from oh_agent.agents.guardrails import MANDATORY_DISCLAIMERS
from oh_agent.agents.workflow_agent import WorkflowAgent
from oh_agent.config import Settings, get_settings
from oh_agent.knowledge.ingestion import ingest_directory
from oh_agent.knowledge.retriever import KnowledgeRetriever
from oh_agent.knowledge.sources import AUTHORITATIVE_SOURCES, KnowledgeSource
from oh_agent.middleware.logging import RequestLoggingMiddleware
from oh_agent.models.audit import AuditEntry
from oh_agent.models.workflow import (
    ComplianceAuditRequest,
    ComplianceAuditResponse,
    ImprovementPlanRequest,
    ImprovementPlanResponse,
    TrendAnalysisRequest,
    TrendAnalysisResponse,
    WorkflowRequest,
    WorkflowResponse,
)
from oh_agent.services.audit_service import AuditService

logger = logging.getLogger(__name__)

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


def _handle_llm_error(exc: Exception) -> None:
    msg = str(exc)
    if "insufficient_quota" in msg or "exceeded" in msg.lower():
        raise HTTPException(402, f"LLM quota exceeded: {msg}") from exc
    if "api key" in msg.lower() or "auth" in msg.lower():
        raise HTTPException(401, f"LLM authentication failed: {msg}") from exc
    if "risk assessment must be confirmed" in msg.lower() or "worker consultation" in msg.lower():
        raise HTTPException(422, str(exc)) from exc
    raise HTTPException(502, f"LLM request failed: {msg}") from exc


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(name)s %(levelname)s %(message)s")

    retriever = KnowledgeRetriever(settings)
    audit = AuditService(settings)

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
    version="0.2.0",
    description=(
        "PDCA-structured occupational health workflow harness for regulated UK environments. "
        "Plan → Do → Check → Act cycle for statutory OH compliance."
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
# Health & info
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
        "version": "0.2.0",
        "framework": "PDCA (Plan-Do-Check-Act)",
        "llm_model": settings.llm_model,
        "disclaimers": MANDATORY_DISCLAIMERS,
    }


# ---------------------------------------------------------------------------
# PLAN + DO — Workflow Generation
# ---------------------------------------------------------------------------


@app.post("/api/v1/workflows", response_model=WorkflowResponse, tags=["plan-do"])
async def generate_workflow(request: WorkflowRequest) -> WorkflowResponse:
    """Generate a PDCA-structured statutory OH workflow.

    Requires risk assessment confirmation and worker consultation
    before any workflow is produced (PLAN gate).
    """
    settings = _get_settings()
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
# CHECK — Compliance Audit
# ---------------------------------------------------------------------------


@app.post("/api/v1/compliance-audit", response_model=ComplianceAuditResponse, tags=["check"])
async def compliance_audit(request: ComplianceAuditRequest) -> ComplianceAuditResponse:
    """Evaluate statutory OH compliance (CHECK phase).

    Assesses employee coverage, surveillance interval adherence,
    and governance arrangements.
    """
    settings = _get_settings()
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
    """Analyse anonymised surveillance data for trends (REVIEW phase).

    Identifies early illness signs, clusters, and control failure indicators.
    """
    settings = _get_settings()
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
    """Generate improvement actions from surveillance findings (ACT phase).

    Outputs feed directly into duty holder's risk management system.
    """
    settings = _get_settings()
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
# Knowledge management
# ---------------------------------------------------------------------------


class KnowledgeStats(BaseModel):
    total_chunks: int
    sources_registered: int


class IngestResponse(BaseModel):
    chunks_ingested: int
    message: str


@app.get("/api/v1/knowledge/sources", response_model=list[KnowledgeSource], tags=["knowledge"])
async def list_sources() -> list[KnowledgeSource]:
    return AUTHORITATIVE_SOURCES


@app.get("/api/v1/knowledge/stats", response_model=KnowledgeStats, tags=["knowledge"])
async def knowledge_stats() -> KnowledgeStats:
    retriever = _get_retriever()
    return KnowledgeStats(
        total_chunks=retriever.collection_count,
        sources_registered=len(AUTHORITATIVE_SOURCES),
    )


@app.post("/api/v1/knowledge/ingest", response_model=IngestResponse, tags=["knowledge"])
async def ingest_knowledge() -> IngestResponse:
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
# Audit trail
# ---------------------------------------------------------------------------


@app.get("/api/v1/audit", response_model=list[AuditEntry], tags=["audit"])
async def get_audit_trail(limit: int = 100) -> list[AuditEntry]:
    audit_svc = _get_audit()
    entries = audit_svc.read_all()
    return entries[-limit:]


@app.get("/api/v1/audit/count", tags=["audit"])
async def audit_count() -> dict[str, int]:
    audit_svc = _get_audit()
    return {"total_entries": audit_svc.count()}
