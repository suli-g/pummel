"""Pipeline controller coordinating StateRepository and ReleaseExecutor."""

from pummel.models.execution import CommandResult, ReleasePayload
from pummel.models.state import (
    PipelineRunCreate,
    PipelineRunRecord,
    PipelineStage,
    PipelineStatus,
)
from pummel.repositories.state_repository import StateRepository
from pummel.services.release_executor import CommandExecutionError, ReleaseExecutor


class PipelineController:
    """Orchestrates pipeline runs across the state repository and release executor."""

    def __init__(
        self,
        state_repository: StateRepository,
        release_executor: ReleaseExecutor,
    ) -> None:
        self._state_repository = state_repository
        self._release_executor = release_executor

    def initialize(self) -> None:
        """Initialize backing persistence schema."""
        self._state_repository.initialize_schema()

    def start_run(self, run_id: str, artifact_path: str | None = None) -> PipelineRunRecord:
        """Create and persist a new pipeline run in RUNNING state."""
        payload = PipelineRunCreate(
            run_id=run_id,
            stage=PipelineStage.INIT,
            status=PipelineStatus.RUNNING,
            artifact_path=artifact_path,
        )
        return self._state_repository.create_run(payload)

    def run_release_step(self, payload: ReleasePayload) -> CommandResult:
        """Execute a release CLI step and record its outcome in state persistence."""
        self._state_repository.update_run_status(
            payload.run_id,
            PipelineStage.RELEASE,
            PipelineStatus.RUNNING,
        )
        try:
            result = self._release_executor.execute_release(payload)
        except (CommandExecutionError, ValueError) as exc:
            self._state_repository.update_run_status(
                payload.run_id,
                PipelineStage.RELEASE,
                PipelineStatus.FAILED,
                error_message=str(exc),
            )
            raise

        if result.succeeded:
            self._state_repository.update_run_status(
                payload.run_id,
                PipelineStage.RELEASE,
                PipelineStatus.SUCCEEDED,
            )
        else:
            self._state_repository.update_run_status(
                payload.run_id,
                PipelineStage.RELEASE,
                PipelineStatus.FAILED,
                error_message=result.stderr or f"Exit code {result.return_code}",
            )
        return result
