"""Unit tests for the SQLite state repository layer."""

from pummel.models.state import PipelineRunCreate, PipelineStage, PipelineStatus
from pummel.repositories.database import SQLiteConnectionManager
from pummel.repositories.state_repository import StateRepository


def test_state_repository_crud_lifecycle() -> None:
    """Verify creating, fetching, updating, and listing pipeline runs in memory."""
    db_manager = SQLiteConnectionManager(":memory:")
    repo = StateRepository(db_manager)
    repo.initialize_schema()

    try:
        created = repo.create_run(
            PipelineRunCreate(
                run_id="run-001",
                stage=PipelineStage.INIT,
                status=PipelineStatus.PENDING,
                artifact_path="design.puml",
            )
        )
        assert created.run_id == "run-001"
        assert created.stage == PipelineStage.INIT
        assert created.status == PipelineStatus.PENDING

        fetched = repo.get_run("run-001")
        assert fetched is not None
        assert fetched.artifact_path == "design.puml"

        updated = repo.update_run_status(
            "run-001",
            PipelineStage.VERIFY,
            PipelineStatus.SUCCEEDED,
        )
        assert updated is not None
        assert updated.stage == PipelineStage.VERIFY
        assert updated.status == PipelineStatus.SUCCEEDED
        assert updated.artifact_path == "design.puml"

        all_runs = repo.list_runs()
        assert len(all_runs) == 1
        assert all_runs[0].run_id == "run-001"
    finally:
        db_manager.close()


def test_state_repository_missing_run_returns_none() -> None:
    """Verify querying or updating a non-existent run returns None."""
    db_manager = SQLiteConnectionManager(":memory:")
    repo = StateRepository(db_manager)
    repo.initialize_schema()

    try:
        assert repo.get_run("missing") is None
        assert (
            repo.update_run_status("missing", PipelineStage.INIT, PipelineStatus.FAILED)
            is None
        )
    finally:
        db_manager.close()
