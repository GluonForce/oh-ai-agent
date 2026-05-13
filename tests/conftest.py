"""Shared test fixtures."""

from __future__ import annotations

import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from oh_agent.config import Settings
from oh_agent.knowledge.retriever import KnowledgeRetriever
from oh_agent.models.hazard import (
    ExposureFrequency,
    ExposureLevel,
    HazardCategory,
    HazardProfile,
)
from oh_agent.models.organisation import DeliveryModel, OrganisationProfile
from oh_agent.services.audit_service import AuditService


@pytest.fixture()
def tmp_dir() -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture()
def settings(tmp_dir: Path) -> Settings:
    return Settings(
        knowledge_dir=tmp_dir / "knowledge",
        chroma_persist_dir=tmp_dir / "chroma",
        audit_log_file=tmp_dir / "audit.jsonl",
        openai_api_key="test-key",
        log_level="DEBUG",
    )


@pytest.fixture()
def retriever(settings: Settings) -> KnowledgeRetriever:
    return KnowledgeRetriever(settings)


@pytest.fixture()
def audit_service(settings: Settings) -> AuditService:
    return AuditService(settings)


@pytest.fixture()
def sample_organisation() -> OrganisationProfile:
    return OrganisationProfile(
        name="Acme Manufacturing Ltd",
        sector="manufacturing",
        tasks=["metal grinding", "spray painting", "solvent cleaning"],
        workforce_size=250,
        workforce_characteristics="Mixed age workforce, includes shift workers",
        multi_site=False,
        delivery_model=DeliveryModel.OHN_LED,
        existing_surveillance="Annual questionnaires only, no biological monitoring",
    )


@pytest.fixture()
def sample_hazards() -> list[HazardProfile]:
    return [
        HazardProfile(
            category=HazardCategory.SKIN,
            hazard_phrase="Wet work — prolonged hand immersion and frequent washing",
            substance_or_agent="water, detergents, solvents",
            exposure_level=ExposureLevel.HIGH,
            exposure_frequency=ExposureFrequency.CONTINUOUS,
        ),
        HazardProfile(
            category=HazardCategory.CHEMICAL,
            hazard_phrase="H334 — May cause allergy or asthma symptoms if inhaled",
            substance_or_agent="isocyanates",
            exposure_level=ExposureLevel.MODERATE,
            exposure_frequency=ExposureFrequency.FREQUENT,
            workplace_exposure_limit="20 µg/m³ NCO (8-hr TWA)",
        ),
    ]


@pytest.fixture()
def client(tmp_dir: Path) -> Iterator[TestClient]:
    """Create a test client with isolated temporary storage."""
    import os

    os.environ["OH_KNOWLEDGE_DIR"] = str(tmp_dir / "knowledge")
    os.environ["OH_CHROMA_PERSIST_DIR"] = str(tmp_dir / "chroma")
    os.environ["OH_AUDIT_LOG_FILE"] = str(tmp_dir / "audit.jsonl")
    os.environ["OH_OPENAI_API_KEY"] = "test-key"

    from oh_agent.main import app

    with TestClient(app) as c:
        yield c

    for key in ["OH_KNOWLEDGE_DIR", "OH_CHROMA_PERSIST_DIR", "OH_AUDIT_LOG_FILE", "OH_OPENAI_API_KEY"]:
        os.environ.pop(key, None)
