# pummel

A PUML-to-Code compiler pipeline engine with SQLite state tracking, validated CLI execution, and skill distribution.

## Install

```bash
uv sync
```

To install `pummel` globally as a `uv` tool:

```bash
uv tool install .
```

## CLI Usage

Initialize the local state database (`.pummel/state.db`):

```bash
uv run pummel
```

Install the `pummel` skill into another project (writes `.agent/skills/pummel/SKILL.md`):

```bash
uv tool run pummel --add-skill
```

Optional flags for `--add-skill`:
- `--skill-dir <path>`: Install to a custom directory instead of `.agent/skills/pummel`.
- `--force`: Overwrite an existing `SKILL.md`.

## Python Usage

```python
from pathlib import Path

from pummel import (
    PipelineController,
    ReleaseExecutor,
    SQLiteConnectionManager,
    StateRepository,
)
from pummel.models import ReleasePayload

db = SQLiteConnectionManager(Path(".pummel") / "state.db")
controller = PipelineController(StateRepository(db), ReleaseExecutor())
controller.initialize()

controller.start_run("run-001", artifact_path="design.puml")
result = controller.run_release_step(
    ReleasePayload(run_id="run-001", binary="plantuml", arguments=["design.puml"])
)
```

Only approved binaries (`git`, `gh`, `plantuml`, `mmdc`) are permitted by `ReleaseExecutor`.

## Development

```bash
uv run pytest
uv run ruff check .
uv run mypy .
```
