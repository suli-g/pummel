"""Pydantic V2 models for CLI execution and release payloads."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CommandRequest(BaseModel):
    """Validated CLI command execution request."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    command: list[str] = Field(..., min_length=1)
    cwd: Path | None = None
    timeout_seconds: float = Field(default=60.0, gt=0.0, le=3600.0)
    env: dict[str, str] | None = None

    @field_validator("command")
    @classmethod
    def validate_command_tokens(cls, value: list[str]) -> list[str]:
        """Ensure the executable and arguments are non-empty strings."""
        if not value[0].strip():
            raise ValueError("Executable token must not be empty or whitespace.")
        return value


class CommandResult(BaseModel):
    """Validated result of an executed CLI command."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    command: list[str]
    return_code: int
    stdout: str
    stderr: str

    @property
    def succeeded(self) -> bool:
        """Return True when the subprocess exited with status code 0."""
        return self.return_code == 0


class ReleasePayload(BaseModel):
    """Validated payload for executing a release or pipeline CLI step."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    run_id: str = Field(..., min_length=1, max_length=128)
    binary: str = Field(..., min_length=1, max_length=128)
    arguments: list[str] = Field(default_factory=list)
    working_dir: Path | None = None
    timeout_seconds: float = Field(default=60.0, gt=0.0, le=3600.0)

    @field_validator("binary")
    @classmethod
    def validate_binary(cls, value: str) -> str:
        """Ensure binary name is trimmed and non-empty."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("Binary name must not be empty.")
        return stripped
