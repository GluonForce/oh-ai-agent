"""Tests for knowledge retrieval and ingestion."""

from __future__ import annotations

from pathlib import Path

from oh_agent.config import Settings
from oh_agent.knowledge.ingestion import _chunk_text, ingest_directory
from oh_agent.knowledge.retriever import KnowledgeRetriever
from oh_agent.knowledge.sources import AUTHORITATIVE_SOURCES


class TestChunking:
    def test_basic_chunking(self) -> None:
        text = "A" * 100
        chunks = _chunk_text(text, chunk_size=30, overlap=10)
        assert len(chunks) >= 3
        assert all(len(c) <= 30 for c in chunks)

    def test_overlap(self) -> None:
        text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        chunks = _chunk_text(text, chunk_size=10, overlap=5)
        assert len(chunks) >= 2
        # Overlapping regions should share content
        if len(chunks) >= 2:
            end_of_first = chunks[0][-5:]
            start_of_second = chunks[1][:5]
            assert end_of_first == start_of_second

    def test_empty_text(self) -> None:
        chunks = _chunk_text("", chunk_size=10, overlap=5)
        assert chunks == []


class TestRetriever:
    def test_add_and_query(self, retriever: KnowledgeRetriever) -> None:
        retriever.add_chunks(
            texts=["Wet work causes occupational dermatitis", "Noise above 85 dB requires audiometry"],
            metadatas=[
                {"source_id": "hse-skin", "source_title": "Skin at Work"},
                {"source_id": "hse-noise", "source_title": "Noise at Work"},
            ],
        )
        assert retriever.collection_count == 2

        results = retriever.query("skin disease from wet work", n_results=1)
        assert len(results) == 1
        assert "dermatitis" in results[0].text.lower()

    def test_empty_collection_query(self, retriever: KnowledgeRetriever) -> None:
        results = retriever.query("anything", n_results=5)
        assert results == []

    def test_reset(self, retriever: KnowledgeRetriever) -> None:
        retriever.add_chunks(
            texts=["test content"],
            metadatas=[{"source_id": "test", "source_title": "Test"}],
        )
        assert retriever.collection_count == 1
        retriever.reset()
        assert retriever.collection_count == 0


class TestIngestion:
    def test_ingest_text_file(self, settings: Settings, retriever: KnowledgeRetriever, tmp_dir: Path) -> None:
        kb_dir = tmp_dir / "knowledge"
        kb_dir.mkdir()
        (kb_dir / "test_guidance.txt").write_text(
            "Health surveillance is required under COSHH Regulation 11 "
            "where workers are exposed to substances hazardous to health. "
            "The purpose is to detect adverse health effects at an early stage."
        )
        settings.knowledge_dir = kb_dir
        count = ingest_directory(settings, retriever, directory=kb_dir)
        assert count > 0
        assert retriever.collection_count > 0

    def test_ingest_missing_directory(self, settings: Settings, retriever: KnowledgeRetriever, tmp_dir: Path) -> None:
        settings.knowledge_dir = tmp_dir / "nonexistent"
        count = ingest_directory(settings, retriever)
        assert count == 0

    def test_ingest_empty_directory(self, settings: Settings, retriever: KnowledgeRetriever, tmp_dir: Path) -> None:
        kb_dir = tmp_dir / "knowledge"
        kb_dir.mkdir()
        count = ingest_directory(settings, retriever, directory=kb_dir)
        assert count == 0


class TestAuthoritativeSources:
    def test_sources_not_empty(self) -> None:
        assert len(AUTHORITATIVE_SOURCES) > 0

    def test_all_sources_have_authority(self) -> None:
        for src in AUTHORITATIVE_SOURCES:
            assert src.authority, f"Source {src.id} has no authority."

    def test_source_ids_unique(self) -> None:
        ids = [s.id for s in AUTHORITATIVE_SOURCES]
        assert len(ids) == len(set(ids)), "Duplicate source IDs found."
