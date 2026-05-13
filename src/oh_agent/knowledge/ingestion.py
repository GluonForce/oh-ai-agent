"""Document ingestion pipeline.

Reads documents from the knowledge_base directory, chunks them, and
upserts them into the vector store with full source provenance.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any

from oh_agent.config import Settings
from oh_agent.knowledge.retriever import KnowledgeRetriever
from oh_agent.knowledge.sources import AUTHORITATIVE_SOURCES, KnowledgeSource

logger = logging.getLogger(__name__)


def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text into overlapping chunks by character count."""
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return [c.strip() for c in chunks if c.strip()]


def _read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _read_docx_file(path: Path) -> str:
    from docx import Document

    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _detect_source(filename: str) -> KnowledgeSource | None:
    """Attempt to match a file to a pre-registered authoritative source."""
    lower = filename.lower()
    for src in AUTHORITATIVE_SOURCES:
        if src.id in lower or any(word in lower for word in src.title.lower().split()[:3]):
            return src
    return None


def ingest_directory(
    settings: Settings,
    retriever: KnowledgeRetriever,
    directory: Path | None = None,
) -> int:
    """Ingest all supported documents from *directory* into the retriever.

    Returns the number of chunks ingested.
    """
    target = directory or settings.knowledge_dir
    if not target.exists():
        logger.warning("Knowledge directory %s does not exist — skipping.", target)
        return 0

    supported = {".txt", ".md", ".docx"}
    total_chunks = 0

    for path in sorted(target.rglob("*")):
        if path.suffix.lower() not in supported or not path.is_file():
            continue

        logger.info("Ingesting %s", path.name)

        text = _read_docx_file(path) if path.suffix.lower() == ".docx" else _read_text_file(path)

        if not text.strip():
            continue

        chunks = _chunk_text(text, settings.chunk_size, settings.chunk_overlap)
        source = _detect_source(path.name)

        metadatas: list[dict[str, Any]] = []
        ids: list[str] = []
        for i, chunk in enumerate(chunks):
            chunk_id = hashlib.sha256(f"{path.name}:{i}:{chunk[:64]}".encode()).hexdigest()[:16]
            meta: dict[str, Any] = {
                "filename": path.name,
                "chunk_index": i,
                "source_id": source.id if source else path.stem,
                "source_title": source.title if source else path.name,
                "source_type": source.source_type.value if source else "unknown",
                "authority": source.authority if source else "user_uploaded",
            }
            metadatas.append(meta)
            ids.append(chunk_id)

        retriever.add_chunks(texts=chunks, metadatas=metadatas, ids=ids)
        total_chunks += len(chunks)
        logger.info("  → %d chunks from %s", len(chunks), path.name)

    return total_chunks
