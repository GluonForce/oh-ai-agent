"""RAG retriever backed by ChromaDB.

Retrieval-augmented generation layer that fetches relevant chunks from
the knowledge base so the LLM can ground its outputs in authoritative
evidence.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb

from oh_agent.config import Settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RetrievedChunk:
    """A chunk returned from the knowledge store with provenance."""

    text: str
    source_id: str
    source_title: str
    distance: float
    metadata: dict[str, Any]


class KnowledgeRetriever:
    """Thin wrapper around ChromaDB for deterministic, auditable retrieval."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        persist_dir = str(settings.chroma_persist_dir)
        persist_path = Path(persist_dir)
        persist_path.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._collection = self._client.get_or_create_collection(
            name=settings.chroma_collection,
            metadata={"hnsw:space": "cosine"},
        )

    @property
    def collection_count(self) -> int:
        return self._collection.count()

    def add_chunks(
        self,
        texts: list[str],
        metadatas: list[dict[str, Any]],
        ids: list[str] | None = None,
    ) -> None:
        """Add text chunks with metadata to the collection."""
        if ids is None:
            ids = [hashlib.sha256(t.encode()).hexdigest()[:16] for t in texts]
        self._collection.upsert(documents=texts, metadatas=metadatas, ids=ids)
        logger.info("Upserted %d chunks into knowledge store.", len(texts))

    def query(self, query_text: str, n_results: int | None = None) -> list[RetrievedChunk]:
        """Retrieve the most relevant chunks for a query string."""
        k = n_results or self._settings.retrieval_top_k
        results = self._collection.query(query_texts=[query_text], n_results=k)

        chunks: list[RetrievedChunk] = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc, meta, dist in zip(documents, metadatas, distances, strict=False):
            chunks.append(
                RetrievedChunk(
                    text=doc,
                    source_id=meta.get("source_id", "unknown"),
                    source_title=meta.get("source_title", "unknown"),
                    distance=dist,
                    metadata=meta,
                )
            )
        return chunks

    def reset(self) -> None:
        """Delete and recreate the collection (for testing)."""
        self._client.delete_collection(self._settings.chroma_collection)
        self._collection = self._client.get_or_create_collection(
            name=self._settings.chroma_collection,
            metadata={"hnsw:space": "cosine"},
        )
