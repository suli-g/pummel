"""Unit tests for ReleaseExecutor service and SubprocessCommandRunner."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from pummel.models.execution import CommandRequest, CommandResult, ReleasePayload
from pummel.services.release_executor import (
    CommandExecutionError,
    ReleaseExecutor,
    SubprocessCommandRunner,
    UnapprovedBinaryError,
)


class FakeCommandRunner:
    """In-memory fake CommandRunner for unit testing ReleaseExecutor without side effects."""

    def __init__(self, result: CommandResult) -> None:
        self._result = result
        self.requests: list[CommandRequest] = []

    def run(self, request: CommandRequest) -> CommandResult:
        """Record the request and return the configured result."""
        self.requests.append(request)
        return self._result


def test_release_executor_executes_approved_binary() -> None:
    """Verify ReleaseExecutor delegates validated payloads to the injected runner."""
    expected = CommandResult(
        command=["git", "status"],
        return_code=0,
        stdout="clean",
        stderr="",
    )
    fake_runner = FakeCommandRunner(expected)
    executor = ReleaseExecutor(runner=fake_runner)

    result = executor.execute_release(
        ReleasePayload(run_id="run-1", binary="git", arguments=["status"])
    )

    assert result == expected
    assert result.succeeded is True
    assert len(fake_runner.requests) == 1
    assert fake_runner.requests[0].command == ["git", "status"]


def test_release_executor_rejects_unapproved_binary() -> None:
    """Verify Dependency Governance allowlist rejects unapproved binaries."""
    fake_runner = FakeCommandRunner(
        CommandResult(command=["curl"], return_code=0, stdout="", stderr="")
    )
    executor = ReleaseExecutor(runner=fake_runner)

    with pytest.raises(UnapprovedBinaryError):
        executor.execute_release(ReleasePayload(run_id="run-2", binary="curl"))

    assert fake_runner.requests == []


def test_command_request_rejects_blank_executable() -> None:
    """Verify Pydantic validation rejects empty or whitespace executable tokens."""
    with pytest.raises(ValidationError):
        CommandRequest(command=["   "])


def test_subprocess_command_runner_enforces_shell_false() -> None:
    """Verify SubprocessCommandRunner invokes subprocess.run with shell=False."""
    mock_completed = MagicMock(returncode=0, stdout="ok", stderr="")
    runner = SubprocessCommandRunner()
    request = CommandRequest(command=["git", "--version"], timeout_seconds=10.0)

    with patch("pummel.services.release_executor.subprocess.run", return_value=mock_completed) as m:
        result = runner.run(request)

    assert result.return_code == 0
    assert result.stdout == "ok"
    m.assert_called_once()
    _, kwargs = m.call_args
    assert kwargs["shell"] is False
    assert kwargs["capture_output"] is True
    assert kwargs["text"] is True


def test_subprocess_command_runner_wraps_timeout() -> None:
    """Verify TimeoutExpired is wrapped in CommandExecutionError."""
    runner = SubprocessCommandRunner()
    request = CommandRequest(command=["git", "fetch"], timeout_seconds=1.0)

    with (
        patch(
            "pummel.services.release_executor.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd=["git", "fetch"], timeout=1.0),
        ),
        pytest.raises(CommandExecutionError),
    ):
        runner.run(request)
