"""CLI execution service with strict Pydantic validation and subprocess encapsulation."""

import subprocess
from typing import Protocol

from pummel.models.execution import CommandRequest, CommandResult, ReleasePayload

APPROVED_BINARIES: frozenset[str] = frozenset({"git", "gh", "plantuml", "mmdc"})


class CommandExecutionError(RuntimeError):
    """Raised when a subprocess fails to start or exceeds its timeout."""


class UnapprovedBinaryError(ValueError):
    """Raised when a command attempts to invoke a binary outside the approved allowlist."""


class CommandRunner(Protocol):
    """Protocol abstracting CLI subprocess execution for dependency injection."""

    def run(self, request: CommandRequest) -> CommandResult:
        """Execute a validated command request and return its structured result."""
        ...


class SubprocessCommandRunner:
    """Default CommandRunner implementation backed by subprocess.run(shell=False)."""

    def run(self, request: CommandRequest) -> CommandResult:
        """Execute the command using subprocess.run with shell=False enforced."""
        try:
            completed = subprocess.run(
                request.command,
                cwd=request.cwd,
                timeout=request.timeout_seconds,
                env=request.env,
                shell=False,
                capture_output=True,
                text=True,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise CommandExecutionError(
                f"Command {request.command!r} timed out after {request.timeout_seconds}s."
            ) from exc
        except OSError as exc:
            raise CommandExecutionError(
                f"Failed to execute command {request.command!r}: {exc}"
            ) from exc

        return CommandResult(
            command=list(request.command),
            return_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )


class ReleaseExecutor:
    """Service responsible for validating and executing approved CLI release commands."""

    def __init__(
        self,
        runner: CommandRunner | None = None,
        *,
        allowed_binaries: frozenset[str] = APPROVED_BINARIES,
    ) -> None:
        self._runner: CommandRunner = runner if runner is not None else SubprocessCommandRunner()
        self._allowed_binaries: frozenset[str] = allowed_binaries

    @property
    def allowed_binaries(self) -> frozenset[str]:
        """Return the immutable set of approved CLI binaries."""
        return self._allowed_binaries

    def execute_command(self, request: CommandRequest) -> CommandResult:
        """Validate a CommandRequest against the binary allowlist and execute it."""
        executable = request.command[0]
        if executable not in self._allowed_binaries:
            raise UnapprovedBinaryError(
                f"Binary {executable!r} is not in the approved allowlist: "
                f"{sorted(self._allowed_binaries)}"
            )
        return self._runner.run(request)

    def execute_release(self, payload: ReleasePayload) -> CommandResult:
        """Validate a ReleasePayload and execute the corresponding CLI command."""
        request = CommandRequest(
            command=[payload.binary, *payload.arguments],
            cwd=payload.working_dir,
            timeout_seconds=payload.timeout_seconds,
        )
        return self.execute_command(request)
