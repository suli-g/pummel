"""Command-line entrypoint for pummel."""

import argparse
from collections.abc import Sequence
from pathlib import Path

from pummel.controllers.pipeline_controller import PipelineController
from pummel.repositories.database import SQLiteConnectionManager
from pummel.repositories.state_repository import StateRepository
from pummel.services.release_executor import ReleaseExecutor
from pummel.services.skill_installer import SkillInstaller


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser for pummel."""
    parser = argparse.ArgumentParser(
        prog="pummel",
        description="Multi-agent PUML-to-Code compiler pipeline.",
    )
    parser.add_argument(
        "--add-skill",
        action="store_true",
        help="Install the bundled pummel SKILL.md into the target project.",
    )
    parser.add_argument(
        "--skill-dir",
        type=Path,
        default=None,
        help="Target directory for --add-skill (default: .agent/skills/pummel).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing SKILL.md when using --add-skill.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the pummel CLI."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.add_skill:
        installer = SkillInstaller()
        result = installer.install(target_dir=args.skill_dir, overwrite=args.force)
        print(f"Installed pummel skill to {result.skill_file}")
        return 0

    db_manager = SQLiteConnectionManager(Path(".pummel") / "state.db")
    repository = StateRepository(db_manager)
    executor = ReleaseExecutor()
    controller = PipelineController(repository, executor)
    controller.initialize()
    return 0
