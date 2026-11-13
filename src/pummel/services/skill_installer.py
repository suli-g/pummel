"""Skill installer service for distributing pummel as a reusable project skill."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict

BUNDLED_SKILL_MD = """---
name: pummel
description: >
  Multi-agent PUML-to-Code compiler pipeline. Use when planning or building
  projects with .pummel/design.puml and .pummel/constraints.bib, or orchestrating
  validated code generation and release steps.
---

# Pummel Skill

Every project must be **planned before it is built**. Use `pummel` to author
architectural contracts in `.pummel/`, track compilation state, and execute
validated CLI steps.

## Workflow

1. **Plan First (`.pummel/` Contracts)**:
   - When building a new project (or adding major features), generate
     `.pummel/design.puml` first before writing implementation code.
   - If external resources, specifications, or libraries are referenced,
     generate `.pummel/constraints.bib` alongside it.
   - Render/validate diagrams using `plantuml` (or `mmdc`) via `ReleaseExecutor`.
2. **Build at the Diagram's Granularity**:
   Match your implementation strategy to the abstraction level of `.pummel/design.puml`:
   - **Flowchart / Activity diagram**: Build the entire end-to-end flow as a cohesive unit.
   - **Component diagram**: Build and verify component by component.
   - **Class diagram**: Build and verify class by class.
   - **Sequence / State diagram**: Build by interaction or state transition.
3. **Track State**:
   - Run `pummel` (or `PipelineController.initialize()`) to prepare `.pummel/state.db`.
   - Record runs and stage transitions (`init`, `parse`, `codegen`, `verify`, `release`)
     through `PipelineController` and `ReleaseExecutor` (`git`, `gh`, `plantuml`, `mmdc`).
4. **Unit Tests & Quality Gates**:
   - Add or update `pytest` unit tests under `tests/` for each unit at the chosen
     granularity, injecting fake/stub dependencies for DB and subprocesses.
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
