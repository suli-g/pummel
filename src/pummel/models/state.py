"""Pydantic V2 models for pipeline state persistence."""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class PipelineStage(StrEnum):
    """Discrete stages of the PUML-to-Code compiler pipeline."""

    INIT = "init"
    PARSE = "parse"
    CODEGEN = "codegen"
    VERIFY = "verify"
    RELEASE = "release"


class PipelineStatus(StrEnum):
    """Execution status of a pipeline run or stage."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class PipelineRunCreate(BaseModel):
    """Input boundary model for creating a new pipeline run record."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    run_id: str = Field(..., min_length=1, max_length=128)
    stage: PipelineStage = PipelineStage.INIT
    status: PipelineStatus = PipelineStatus.PENDING
    artifact_path: str | None = Field(default=None, max_length=512)
    error_message: str | None = Field(default=None, max_length=4096)


class PipelineRunRecord(BaseModel):
    """Persisted pipeline run state record."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    run_id: str = Field(..., min_length=1, max_length=128)
    stage: PipelineStage
    status: PipelineStatus
    artifact_path: str | None = None
    error_message: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
