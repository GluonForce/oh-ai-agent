"""Tests for FastAPI endpoints (PDCA framework, no LLM calls)."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestHealthEndpoint:
    def test_health_returns_200(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "knowledge_chunks" in data

    def test_health_development_env(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.json()["environment"] == "development"


class TestInfoEndpoint:
    def test_info_returns_200(self, client: TestClient) -> None:
        resp = client.get("/info")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "OH AI Agent"
        assert data["framework"] == "PDCA (Plan-Do-Check-Act)"
        assert "disclaimers" in data
        assert len(data["disclaimers"]) >= 3


class TestKnowledgeEndpoints:
    def test_list_sources(self, client: TestClient) -> None:
        resp = client.get("/api/v1/knowledge/sources")
        assert resp.status_code == 200
        sources = resp.json()
        assert len(sources) > 0

    def test_knowledge_stats(self, client: TestClient) -> None:
        resp = client.get("/api/v1/knowledge/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_chunks" in data

    def test_ingest_empty_knowledge_base(self, client: TestClient) -> None:
        resp = client.post("/api/v1/knowledge/ingest")
        assert resp.status_code == 200


class TestAuditEndpoints:
    def test_audit_trail_empty(self, client: TestClient) -> None:
        resp = client.get("/api/v1/audit")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_audit_count(self, client: TestClient) -> None:
        resp = client.get("/api/v1/audit/count")
        assert resp.status_code == 200
        assert "total_entries" in resp.json()


class TestWorkflowValidation:
    def test_workflow_rejects_empty_hazards(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/workflows",
            json={
                "organisation": {"name": "Test", "sector": "test"},
                "hazards": [],
                "risk_assessment": {
                    "risk_assessment_completed": True,
                    "workers_consulted": True,
                },
            },
        )
        assert resp.status_code == 422

    def test_workflow_rejects_missing_risk_assessment(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/workflows",
            json={
                "organisation": {"name": "Test", "sector": "test"},
                "hazards": [{"category": "chemical", "hazard_phrase": "test"}],
            },
        )
        assert resp.status_code == 422

    def test_workflow_rejects_missing_org(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/workflows",
            json={
                "hazards": [{"category": "chemical", "hazard_phrase": "test"}],
                "risk_assessment": {
                    "risk_assessment_completed": True,
                    "workers_consulted": True,
                },
            },
        )
        assert resp.status_code == 422


class TestComplianceAuditValidation:
    def test_rejects_empty_hazards(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/compliance-audit",
            json={
                "organisation": {"name": "Test", "sector": "test"},
                "hazards": [],
            },
        )
        assert resp.status_code == 422


class TestTrendAnalysisValidation:
    def test_rejects_missing_surveillance_summary(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/trend-analysis",
            json={
                "organisation": {"name": "Test", "sector": "test"},
                "hazards": [{"category": "chemical", "hazard_phrase": "test"}],
            },
        )
        assert resp.status_code == 422


class TestImprovementPlanValidation:
    def test_rejects_missing_findings(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/improvement-plan",
            json={
                "organisation": {"name": "Test", "sector": "test"},
                "hazards": [{"category": "chemical", "hazard_phrase": "test"}],
            },
        )
        assert resp.status_code == 422


class TestOpenAPISchema:
    def test_openapi_available(self, client: TestClient) -> None:
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        schema = resp.json()
        assert schema["info"]["title"] == "OH AI Agent"
        assert "/api/v1/workflows" in schema["paths"]
        assert "/api/v1/compliance-audit" in schema["paths"]
        assert "/api/v1/trend-analysis" in schema["paths"]
        assert "/api/v1/improvement-plan" in schema["paths"]
