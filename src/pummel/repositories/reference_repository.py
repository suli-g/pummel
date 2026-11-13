"""Repository for storing BibTeX references in SQLite with optional sqlite-vec indexing."""

import sqlite3
from datetime import datetime
from typing import Protocol

from pummel.models.rag import BibReference, ReferenceSearchResult
from pummel.repositories.database import DatabaseConnectionManager


class VectorIndexBackend(Protocol):
    """Protocol for an optional sqlite-vec vector index backend."""

    def initialize(self, conn: sqlite3.Connection, dimension: int) -> None:
        """Create or verify the vector virtual table on the given SQLite connection."""
        ...

    def upsert_vector(
        self, conn: sqlite3.Connection, cite_key: str, embedding: list[float]
    ) -> None:
        """Store or update the embedding vector for a reference cite_key."""
        ...

    def query_similar(
        self, conn: sqlite3.Connection, query_embedding: list[float], top_k: int
    ) -> list[tuple[str, float]]:
        """Return (cite_key, distance) pairs ordered by similarity."""
        ...


class ReferenceRepository:
    """Stores research/dependency references in SQLite before optional vector indexing."""

    _CREATE_TABLE_SQL = """
        CREATE TABLE IF NOT EXISTS bib_references (
            cite_key TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            access_date TEXT NOT NULL,
            notes TEXT,
            raw_bibtex TEXT,
            created_at TEXT NOT NULL
        );
    """

    def __init__(
        self,
        connection_manager: DatabaseConnectionManager,
        vector_backend: VectorIndexBackend | None = None,
        *,
        embedding_dimension: int = 384,
    ) -> None:
        self._connection_manager = connection_manager
        self._vector_backend = vector_backend
        self._embedding_dimension = embedding_dimension

    def initialize_schema(self) -> None:
        """Create the bib_references table and optional vector index."""
        with self._connection_manager.connection() as conn:
            conn.execute(self._CREATE_TABLE_SQL)
            if self._vector_backend is not None:
                self._vector_backend.initialize(conn, self._embedding_dimension)

    def upsert_reference(
        self,
        reference: BibReference,
        *,
        embedding: list[float] | None = None,
    ) -> BibReference:
        """Persist a reference in bib_references and optionally index its embedding."""
        with self._connection_manager.connection() as conn:
            conn.execute(
                """
                INSERT INTO bib_references (
                    cite_key, title, url, access_date, notes, raw_bibtex, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(cite_key) DO UPDATE SET
                    title = excluded.title,
                    url = excluded.url,
                    access_date = excluded.access_date,
                    notes = excluded.notes,
                    raw_bibtex = excluded.raw_bibtex;
                """,
                (
                    reference.cite_key,
                    reference.title,
                    reference.url,
                    reference.access_date,
                    reference.notes,
                    reference.raw_bibtex,
                    reference.created_at.isoformat(),
                ),
            )
            if embedding is not None and self._vector_backend is not None:
                self._vector_backend.upsert_vector(conn, reference.cite_key, embedding)
        return reference

    def get_reference(self, cite_key: str) -> BibReference | None:
        """Retrieve a stored reference by its BibTeX cite_key."""
        with self._connection_manager.connection() as conn:
            cursor = conn.execute(
                """
                SELECT cite_key, title, url, access_date, notes, raw_bibtex, created_at
                FROM bib_references
                WHERE cite_key = ?;
                """,
                (cite_key,),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_reference(row)

    def list_references(self) -> list[BibReference]:
        """Return all stored references ordered by creation time descending."""
        with self._connection_manager.connection() as conn:
            cursor = conn.execute(
                """
                SELECT cite_key, title, url, access_date, notes, raw_bibtex, created_at
                FROM bib_references
                ORDER BY created_at DESC;
                """
            )
            rows = cursor.fetchall()
        return [self._row_to_reference(row) for row in rows]

    def search_similar(
        self,
        query_embedding: list[float],
        *,
        top_k: int = 5,
    ) -> list[ReferenceSearchResult]:
        """Search references using the configured vector backend."""
        if self._vector_backend is None:
            raise RuntimeError("No VectorIndexBackend configured for vector similarity search.")

        with self._connection_manager.connection() as conn:
            matches = self._vector_backend.query_similar(conn, query_embedding, top_k)

        results: list[ReferenceSearchResult] = []
        for cite_key, distance in matches:
            ref = self.get_reference(cite_key)
            if ref is not None:
                results.append(ReferenceSearchResult(reference=ref, distance=distance))
        return results

    @staticmethod
    def _row_to_reference(row: sqlite3.Row) -> BibReference:
        return BibReference(
            cite_key=str(row["cite_key"]),
            title=str(row["title"]),
            url=str(row["url"]),
            access_date=str(row["access_date"]),
            notes=str(row["notes"]) if row["notes"] is not None else None,
            raw_bibtex=str(row["raw_bibtex"]) if row["raw_bibtex"] is not None else None,
            created_at=datetime.fromisoformat(str(row["created_at"])),
        )
