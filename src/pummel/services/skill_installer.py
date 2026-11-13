"""Skill installer service for distributing pummel as a reusable project skill."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict

BUNDLED_SKILL_MD = """---
name: pummel
description: >
  Multi-agent PUML-to-Code compiler pipeline. Use when working with design.puml,
  constraints.bib, or orchestrating validated code generation and release steps.
---

# Pummel Skill

Use `pummel` to manage PUML-to-Code compilation runs, state persistence, and
validated CLI execution.

## Workflow

1. **Contracts**: Ensure `design.puml` and `constraints.bib` are present in the
   project root.
2. **Initialize State**: Run `pummel` (or `PipelineController.initialize()`) to
   prepare `.pummel/state.db`.
3. **Execute Steps**: Use `PipelineController` and `ReleaseExecutor` with
   `ReleasePayload` for approved CLI binaries (`git`, `gh`, `plantuml`, `mmdc`).
4. **Unit Tests & Quality Gates**:
   - Add or update `pytest` unit tests under `tests/` for every generated or
     modified module, injecting fake/stub dependencies for DB and subprocesses.
   - Run `uv run pytest`, `uv run ruff check .`, and `uv run mypy .` before
     completing a stage.
"""


class SkillInstallResult(BaseModel):
    """Validated result of installing the bundled pummel skill."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    skill_file: Path
    overwritten: bool


class SkillInstaller:
    """Service that installs the bundled pummel SKILL.md into a target project."""

    def __init__(self, skill_content: str = BUNDLED_SKILL_MD) -> None:
        self._skill_content = skill_content

    def install(
        self,
        target_dir: Path | None = None,
        *,
        overwrite: bool = False,
    ) -> SkillInstallResult:
        """Write SKILL.md into target_dir (defaults to ./.agent/skills/pummel)."""
        destination_dir = (
            target_dir if target_dir is not None else Path.cwd() / ".agent" / "skills" / "pummel"
        )
        skill_file = destination_dir / "SKILL.md"
        existed = skill_file.exists()

        if existed and not overwrite:
            raise FileExistsError(
                f"Skill file already exists at {skill_file}. Pass --force to overwrite."
            )

        destination_dir.mkdir(parents=True, exist_ok=True)
        skill_file.write_text(self._skill_content, encoding="utf-8")
        return SkillInstallResult(skill_file=skill_file, overwritten=existed)
