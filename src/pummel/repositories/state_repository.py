"""State repository abstracting SQLite queries for pipeline runs."""

import sqlite3
from datetime import UTC, datetime

from pummel.models.state import (
    PipelineRunCreate,
    PipelineRunRecord,
    PipelineStage,
    PipelineStatus,
)
from pummel.repositories.database import DatabaseConnectionManager


class StateRepository:
    """Repository encapsulating all SQL persistence for pipeline run state."""

    _CREATE_TABLE_SQL = """
        CREATE TABLE IF NOT EXISTS pipeline_runs (
            run_id TEXT PRIMARY KEY,
            stage TEXT NOT NULL,
            status TEXT NOT NULL,
            artifact_path TEXT,
            error_message TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
    """

    def __init__(self, connection_manager: DatabaseConnectionManager) -> None:
        self._connection_manager = connection_manager

    def initialize_schema(self) -> None:
        """Create required database tables if they do not already exist."""
        with self._connection_manager.connection() as conn:
            conn.execute(self._CREATE_TABLE_SQL)

    def create_run(self, payload: PipelineRunCreate) -> PipelineRunRecord:
        """Persist a new pipeline run record and return the stored model."""
        now = datetime.now(UTC)
        now_iso = now.isoformat()
        with self._connection_manager.connection() as conn:
            conn.execute(
                """
                INSERT INTO pipeline_runs (
                    run_id, stage, status, artifact_path, error_message, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    payload.run_id,
                    payload.stage.value,
                    payload.status.value,
                    payload.artifact_path,
                    payload.error_message,
                    now_iso,
                    now_iso,
                ),
            )
        return PipelineRunRecord(
            run_id=payload.run_id,
            stage=payload.stage,
            status=payload.status,
            artifact_path=payload.artifact_path,
            error_message=payload.error_message,
            created_at=now,
            updated_at=now,
        )

    def get_run(self, run_id: str) -> PipelineRunRecord | None:
        """Retrieve a pipeline run record by its unique identifier."""
        with self._connection_manager.connection() as conn:
            cursor = conn.execute(
                """
                SELECT run_id, stage, status, artifact_path, error_message, created_at, updated_at
                FROM pipeline_runs
                WHERE run_id = ?;
                """,
                (run_id,),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_record(row)

    def update_run_status(
        self,
        run_id: str,
        stage: PipelineStage,
        status: PipelineStatus,
        *,
        artifact_path: str | None = None,
        error_message: str | None = None,
    ) -> PipelineRunRecord | None:
        """Update the stage, status, and optional metadata of an existing run."""
        updated_at = datetime.now(UTC).isoformat()
        with self._connection_manager.connection() as conn:
            cursor = conn.execute(
                """
                UPDATE pipeline_runs
                SET stage = ?,
                    status = ?,
                    artifact_path = COALESCE(?, artifact_path),
                    error_message = ?,
                    updated_at = ?
                WHERE run_id = ?;
                """,
                (
                    stage.value,
                    status.value,
                    artifact_path,
                    error_message,
                    updated_at,
                    run_id,
                ),
            )
            if cursor.rowcount == 0:
                return None
        return self.get_run(run_id)

    def list_runs(self) -> list[PipelineRunRecord]:
        """Return all persisted pipeline runs ordered by creation time descending."""
        with self._connection_manager.connection() as conn:
            cursor = conn.execute(
                """
                SELECT run_id, stage, status, artifact_path, error_message, created_at, updated_at
                FROM pipeline_runs
                ORDER BY created_at DESC;
                """
            )
            rows = cursor.fetchall()
        return [self._row_to_record(row) for row in rows]

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> PipelineRunRecord:
        return PipelineRunRecord(
            run_id=str(row["run_id"]),
            stage=PipelineStage(str(row["stage"])),
            status=PipelineStatus(str(row["status"])),
            artifact_path=str(row["artifact_path"]) if row["artifact_path"] is not None else None,
            error_message=str(row["error_message"]) if row["error_message"] is not None else None,
            created_at=datetime.fromisoformat(str(row["created_at"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
        )
