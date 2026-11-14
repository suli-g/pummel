"""Skill installer service for distributing pummel as a reusable project skill."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict

BUNDLED_SKILL_MD = """---
name: pummel
description: >
  Plan-first software design and implementation workflow using PlantUML diagrams
  in .pummel/ and BibTeX references in .pummel/constraints.bib.
---

# Pummel Workflow

Every project must be **planned before it is built**. Follow these five
processes in order before and during implementation.

## 1. Feedback & Discovery Process

Users may communicate requirements in different ways—adapt to their style and
document what is given:
- **Holistic description**: Describes the entire system end-to-end without explicit roles.
- **Role-driven description**: Describes distinct actors, personas, or user roles.
- **Constraint / Architecture-first**: Specifies technical boundaries, stacks, or patterns up front.

Always pause for explicit user feedback at key decision points:
- **Architecture style**: Ask the user what architecture style they want (e.g., OOP,
  functional, layered, event-driven). If OOP, model the system with a class diagram.
- **Build granularity**: Ask the user at what level/granularity they want the project
  to be built from.
- **Building cadence & further breakdown**: Once UML diagrams are generated (or if UML
  already exists), ask the user to choose the building cadence (e.g., step-by-step
  with review checkpoints, component-by-component batches, or full end-to-end) and
  invite them to suggest further breakdowns of specific components before building.
- **External dependencies**: Prompt the user before adopting any external library,
  service, or binary.

## 2. Diagram Creation Process (`.pummel/`)

Decompose the system into PlantUML diagrams before writing implementation code:
1. **Roles**: Identify all user roles from the prompt. If none are described,
   **assume a single role**.
2. **Context diagrams** (`.pummel/systems/contexts/`): For each role, map the user
   to the holistic system.
3. **Use case diagrams** (`.pummel/systems/use-cases/`): For each system, create
   use case diagrams.
4. **Sequence diagrams** (`.pummel/systems/sequences/`): For each use case, create
   a sequence diagram.
5. **Architecture diagram** (`.pummel/design.puml`): Once the user selects an
   architecture style (e.g., a class diagram for OOP), produce the structural
   diagram at the agreed granularity. If the user requests further breakdowns of
   specific components, refine the diagrams before proceeding.

## 3. Research Process

Begin the research phase **only after** the diagrams are mapped:
- Investigate algorithms, patterns, APIs, and candidate dependencies needed to
  satisfy the mapped diagrams.
- Do not install or import any external dependency without first prompting the
  user and receiving approval.

## 4. Referencing Process (`.pummel/constraints.bib`)

Record every approved external dependency, specification, or reference in
`.pummel/constraints.bib` using BibTeX format. Each entry must include at minimum:
- `url`: The link to the resource or package documentation.
- `urldate`: The date the resource was accessed (e.g., `2026-11-13`).

## 5. Implementation Process

Build the project strictly according to the granularity and **building cadence**
chosen by the user:
- **Flowchart / Activity diagram**: Build the entire end-to-end flow as a cohesive unit.
- **Component diagram**: Build and verify component by component.
- **Class diagram**: Build and verify class by class.
- **Sequence / State diagram**: Build by interaction or state transition.

Follow the user's chosen cadence (e.g., pausing after each component/unit for review
or refinement if requested), add unit tests as appropriate for each implemented unit,
and verify that tests and project checks pass before moving to the next unit.
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
