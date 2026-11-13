"""Skill installer service for distributing pummel as a reusable project skill."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict

BUNDLED_SKILL_MD = """---
name: pummel
description: >
  Multi-agent PUML-to-Code compiler pipeline. Use when planning or building
  projects with .pummel/ diagrams, .pummel/constraints.bib, or orchestrating
  validated code generation and release steps.
---

# Pummel Skill

Every project must be **planned before it is built**. Use `pummel` to decompose
requirements into `.pummel/` diagrams, record external references in `.bib` and
SQLite, track compilation state, and build at the user's chosen granularity.

## User Communication Modes

Users may interact with an agent in different ways—adapt and document the input:
- **Holistic description**: Describes the entire system end-to-end without naming roles.
- **Role-driven description**: Describes distinct actors, personas, or user roles.
- **Constraint / Architecture-first**: Specifies technical boundaries, stacks, or patterns up front.

## Workflow

1. **Decompose Roles & Systems (`.pummel/systems/`)**:
   - Identify all user roles in the prompt; if none are described, **assume a single role**.
   - For each role, create a **context diagram** mapping the user to the holistic system
     in `.pummel/systems/contexts/`.
   - For each system, create **use case diagrams** in `.pummel/systems/use-cases/`.
   - For each use case, create a **sequence diagram** in `.pummel/systems/sequences/`.
2. **Confirm Architecture & Build Granularity**:
   - **Ask the user** which architecture style they want (e.g., OOP, functional, layered).
     If **OOP**, describe the system using a **class diagram** (e.g., `.pummel/design.puml`).
   - **Ask the user** the granularity/level at which they want to build:
     - **Flowchart / Activity diagram**: Build the entire end-to-end flow.
     - **Component diagram**: Build and verify component by component.
     - **Class diagram**: Build and verify class by class.
     - **Sequence / State diagram**: Build by interaction or state transition.
3. **Research Phase & External Dependencies (`.pummel/constraints.bib`)**:
   - Begin the research phase only after the diagrams are mapped.
   - If an external dependency is required, **prompt the user** for explicit approval
     before adopting it.
   - If approved, create a BibTeX reference in `.pummel/constraints.bib` containing at
     minimum the resource **link (`url`)** and **access date (`urldate`)**, and store
     it in the `bib_references` SQLite table via `ReferenceRepository` before RAG indexing.
4. **Track State & Execute**:
   - Run `pummel` (or `PipelineController.initialize()`) to prepare `.pummel/state.db`.
   - Record runs and stage transitions through `PipelineController` and `ReleaseExecutor`
     (`git`, `gh`, `plantuml`, `mmdc`).
5. **Unit Tests & Quality Gates**:
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
