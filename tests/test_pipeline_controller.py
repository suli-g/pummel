"""Unit tests for PipelineController orchestration."""

from pummel.controllers.pipeline_controller import PipelineController
from pummel.models.execution import CommandRequest, CommandResult, ReleasePayload
from pummel.models.state import PipelineStage, PipelineStatus
from pummel.repositories.database import SQLiteConnectionManager
from pummel.repositories.state_repository import StateRepository
from pummel.services.release_executor import ReleaseExecutor


class StubRunner:
    """Stub CommandRunner returning a deterministic CommandResult."""

    def __init__(self, return_code: int, stderr: str = "") -> None:
        self._return_code = return_code
        self._stderr = stderr

    def run(self, request: CommandRequest) -> CommandResult:
        """Return a deterministic result for the given request."""
        return CommandResult(
            command=list(request.command),
            return_code=self._return_code,
            stdout="",
            stderr=self._stderr,
        )


def test_pipeline_controller_release_success() -> None:
    """Verify controller transitions run to SUCCEEDED when release command passes."""
    db_manager = SQLiteConnectionManager(":memory:")
    repo = StateRepository(db_manager)
    executor = ReleaseExecutor(runner=StubRunner(return_code=0))
    controller = PipelineController(repo, executor)
    controller.initialize()

    try:
        controller.start_run("run-100", artifact_path="design.puml")
        result = controller.run_release_step(
            ReleasePayload(run_id="run-100", binary="plantuml", arguments=["design.puml"])
        )
        assert result.succeeded is True

        record = repo.get_run("run-100")
        assert record is not None
        assert record.stage == PipelineStage.RELEASE
        assert record.status == PipelineStatus.SUCCEEDED
    finally:
        db_manager.close()


def test_pipeline_controller_release_failure() -> None:
    """Verify controller transitions run to FAILED when release command returns non-zero."""
    db_manager = SQLiteConnectionManager(":memory:")
    repo = StateRepository(db_manager)
    executor = ReleaseExecutor(runner=StubRunner(return_code=1, stderr="syntax error"))
    controller = PipelineController(repo, executor)
    controller.initialize()

    try:
        controller.start_run("run-101")
        result = controller.run_release_step(
            ReleasePayload(run_id="run-101", binary="mmdc", arguments=["-i", "diagram.mmd"])
        )
        assert result.succeeded is False

        record = repo.get_run("run-101")
        assert record is not None
        assert record.stage == PipelineStage.RELEASE
        assert record.status == PipelineStatus.FAILED
        assert record.error_message == "syntax error"
    finally:
        db_manager.close()
