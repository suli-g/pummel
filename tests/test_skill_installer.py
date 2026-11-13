"""Unit tests for SkillInstaller and the --add-skill CLI flag."""

from pathlib import Path

import pytest

from pummel.cli import main
from pummel.services.skill_installer import SkillInstaller


def test_skill_installer_writes_skill_md(tmp_path: Path) -> None:
    """Verify SkillInstaller creates SKILL.md and prevents accidental overwrites."""
    target_dir = tmp_path / ".agent" / "skills" / "pummel"
    installer = SkillInstaller()

    result = installer.install(target_dir=target_dir)
    assert result.skill_file == target_dir / "SKILL.md"
    assert result.overwritten is False
    content = result.skill_file.read_text(encoding="utf-8")
    assert "name: pummel" in content
    assert ".pummel/design.puml" in content
    assert ".pummel/constraints.bib" in content
    assert "Component diagram" in content
    assert "Class diagram" in content

    with pytest.raises(FileExistsError):
        installer.install(target_dir=target_dir)

    overwritten = installer.install(target_dir=target_dir, overwrite=True)
    assert overwritten.overwritten is True


def test_cli_add_skill_installs_into_custom_dir(tmp_path: Path) -> None:
    """Verify pummel --add-skill --skill-dir installs SKILL.md via CLI."""
    skill_dir = tmp_path / "custom_skills" / "pummel"
    exit_code = main(["--add-skill", "--skill-dir", str(skill_dir)])

    assert exit_code == 0
    assert (skill_dir / "SKILL.md").is_file()
