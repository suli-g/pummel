"""Unit tests for ReferenceRepository and BibReference validation."""

import sqlite3

import pytest
from pydantic import ValidationError

from pummel.models.rag import BibReference
from pummel.repositories.database import SQLiteConnectionManager
from pummel.repositories.reference_repository import ReferenceRepository


class FakeVectorBackend:
    """In-memory stub for sqlite-vec vector operations."""

    def __init__(self) -> None:
        self.vectors: dict[str, list[float]] = {}

    def initialize(self, conn: sqlite3.Connection, dimension: int) -> None:
        """No-op schema initialization for stub backend."""
        _ = (conn, dimension)

    def upsert_vector(
        self, conn: sqlite3.Connection, cite_key: str, embedding: list[float]
    ) -> None:
        """Store vector in memory."""
        _ = conn
        self.vectors[cite_key] = embedding

    def query_similar(
        self, conn: sqlite3.Connection, query_embedding: list[float], top_k: int
    ) -> list[tuple[str, float]]:
        """Return stored keys with dummy distance 0.1."""
        _ = (conn, query_embedding)
        return [(key, 0.1) for key in list(self.vectors)[:top_k]]


def test_reference_repository_stores_and_retrieves_bib_references() -> None:
    """Verify references are stored in bib_references table and searchable via backend."""
    db_manager = SQLiteConnectionManager(":memory:")
    backend = FakeVectorBackend()
    repo = ReferenceRepository(db_manager, vector_backend=backend, embedding_dimension=3)
    repo.initialize_schema()

    try:
        ref = BibReference(
            cite_key="sqlite_vec_2026",
            title="sqlite-vec: A vector search SQLite extension",
            url="https://github.com/asg017/sqlite-vec",
            access_date="2026-11-13",
            notes="Approved for local RAG vector storage.",
        )
        repo.upsert_reference(ref, embedding=[0.1, 0.2, 0.3])

        fetched = repo.get_reference("sqlite_vec_2026")
        assert fetched is not None
        assert fetched.url == "https://github.com/asg017/sqlite-vec"
        assert fetched.access_date == "2026-11-13"

        all_refs = repo.list_references()
        assert len(all_refs) == 1

        matches = repo.search_similar([0.1, 0.2, 0.3], top_k=5)
        assert len(matches) == 1
        assert matches[0].reference.cite_key == "sqlite_vec_2026"
        assert matches[0].distance == 0.1
    finally:
        db_manager.close()


def test_bib_reference_requires_non_blank_url_and_access_date() -> None:
    """Verify BibReference rejects blank url or access_date."""
    with pytest.raises(ValidationError):
        BibReference(
            cite_key="bad_ref",
            title="Missing URL",
            url="   ",
            access_date="2026-11-13",
        )

    with pytest.raises(ValidationError):
        BibReference(
            cite_key="bad_ref_2",
            title="Missing Access Date",
            url="https://example.com",
            access_date="",
        )
